#!/usr/bin/python3

import os
import sys

DISKS_PATH_SYS = ["/sys/class/block", "/sys/block"]
DRIVE_PATH_MASK = "{}/{}/{}"
DEVICE_PATH_MASK = "{}/{}/device"
LVS_PATH_NAME = "{}/{}/dm/name"
MOUNTS_PATH = "/proc/mounts"


class Mounts(object):
  def __init__(self):
    mounts = []
    self._mounts = dict()

    try:
      with open(MOUNTS_PATH, "r") as f:
        mounts = [line.rstrip(os.linesep) for line in f]
    except IOError:
      pass

    self._parse_mounts(mounts)

  def _parse_mounts(self, mounts: [str]):
    for mount in mounts:
      if not mount or not mount.startswith("/dev"):
        continue

      m_device, m_location, m_fs, m_options, _, _ = mount.split(" ")
      m_device = m_device.split("/dev/")[1].rstrip("1234567890")

      if m_device not in self._mounts:
        self._mounts[m_device] = []

      device_partitions = self._mounts[m_device]
      device_partitions.append({
        "mount": m_location,
        "fs": m_fs,
        "options": m_options.split(",")
      })

  def is_mounted(self, device_name: str, lvs_names: list = None) -> bool:
    lvs_mounted = False
    if lvs_names:
      for name in lvs_names:
        if "mapper/{}".format(name) in self._mounts:
          lvs_mounted = True
          break
    return lvs_mounted or device_name in self._mounts

  def get_mount_points(self, device_name: str) -> list:
    if device_name not in self._mounts:
      return []

    return [dev["mount"] for dev in self._mounts[device_name]]


class LVSDrive(object):
  def _loaddata(self, rel_path: str) -> str or None:
    try:
      with open(DRIVE_PATH_MASK.format(self.__info_root, self.drive, rel_path), "r") as f:
        return f.readline().strip(os.linesep)
    except IOError:
      return None

  def __init__(self, info_root: str, drive: str):
    self.__info_root = info_root
    self.drive = drive

    self.lvname = self._loaddata("dm/name")
    self.disks = set([d.rstrip("1234567890") for d in os.listdir("{}/{}/slaves".format(info_root, drive))])


class Drive(object):

  def _loaddata(self, rel_path: str) -> str or None:
    try:
      with open(DRIVE_PATH_MASK.format(self.__info_root, self.drive, rel_path), "r") as f:
        return f.readline().strip(os.linesep)
    except IOError:
      return None

  def human_size(self, logical_block_size: int, origin_bytes: int):
    sizes = ["Kb", "Mb", "Gb", "Tb", "Pb"]

    size = origin_bytes * logical_block_size
    for unit in sizes:
      size = size / 1024
      if (round(size)) > 999:
        continue

      return "{:.3f} {}".format(size, unit)

  def __init__(self, info_root: str, drive: str, mounts: Mounts):
    self._mounts = mounts
    self.__info_root = info_root
    self.drive: str = drive
    self.model: str = self._loaddata("device/model")
    self.capacity_blocks: int = int(self._loaddata("size"))
    self.logical_block_size: int = int(self._loaddata("queue/logical_block_size"))
    self.size: str = self.human_size(self.logical_block_size, self.capacity_blocks)
    self.is_lvs: bool = False
    self.lvs_names: list = []

  def __lt__(self, other):
    return self.drive < other.drive

  def __str__(self) -> str:
    options_str = []
    if self._mounts.is_mounted(self.drive, self.lvs_names):
      mounts = self._mounts.get_mount_points(self.drive)
      if mounts:
        options_str.append("mounted: {}".format(",".join(mounts)))
      else:
        options_str.append("mounted")

    if self.is_lvs:
      options_str.append("lvs: {}".format(",".join(self.lvs_names)))

    return "{:4s}: {:16s}  {:10s}  ({})".format(self.drive, self.model, self.size, "; ".join(options_str))


def is_drive(info_root: str, s: str) -> bool:
  return os.path.exists(DEVICE_PATH_MASK.format(info_root, s))


def is_lvs(info_root: str, s: str) -> bool:
  return s.startswith("dm") and os.path.exists(LVS_PATH_NAME.format(info_root, s))


def main():
  argv = sys.argv
  info_root = DISKS_PATH_SYS[0]

  if not os.path.exists(info_root):
    for path in DISKS_PATH_SYS:
      if os.path.exists(path):
        info_root = path
        break

  if not os.path.exists(info_root):
    print("Your system is not supported, sorry")
    sys.exit(1)

  mounts = Mounts()
  system_drives = []
  lvs_drives = dict()
  for drive in os.listdir(info_root):
    if is_drive(info_root, drive):
      system_drives.append(Drive(info_root, drive, mounts))
    elif is_lvs(info_root, drive):
      lvs_drive = LVSDrive(info_root, drive)
      for d in lvs_drive.disks:
        if d not in lvs_drives:
          lvs_drives[d] = [lvs_drive.lvname]
        else:
          lvs_drives[d].append(lvs_drive.lvname)

  for drive in system_drives:
    if drive.drive in lvs_drives:
      drive.is_lvs = True
      drive.lvs_names = lvs_drives[drive.drive]

  system_drives = sorted(system_drives)

  for drive in system_drives:
    print(drive)

  print("----Total: {}".format(len(system_drives)))


if __name__ == '__main__':
  main()
