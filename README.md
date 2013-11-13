# virt-config

## About

virt-config can update configuration of a virtual machine via libvirt and guestfs.

## Setup

### Install Dependencies

    $ sudo apt-get install libguestfs0 libguestfs-tools python-guestfs
    $ sudo update-guestfs-appliance

### Get Sources

    $ git clone https://github.com/akagisho/virt-config
    $ cd virt-config
    $ chmod +x virt-config.py

## Usage

    Usage:
        virt-config.py [options] domname
    Options:
        -i new_ipaddr: update ip-address
        -h new_hostname update hostname
        -c: confirm result

## Supported OSs as Guest

+ Ubuntu
