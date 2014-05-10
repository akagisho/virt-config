# virt-config

## About

virt-config can update configuration of a virtual machine via libvirt and guestfs.

## Setup

### Install Dependencies

    $ sudo apt-get install libguestfs0 libguestfs-tools python-guestfs
    $ sudo update-guestfs-appliance

### Get Sources

    $ git clone https://github.com/akagisho/virt-config

## Usage

    Usage:
        virt-config.py [options] domname
    Options:
        -i new_ipaddr: update ip-address
        -h new_hostname: update hostname
        -c: confirm result

## Example

First, clone a VM as usual.

    $ sudo virt-clone \
        --original tmpl-ubuntu1204 \
        --file /var/lib/libvirt/images/new-machine.img \
        --name new-machine

Update ip-address and hostname.

    $ sudo ./virt-config.py \
        -i 192.168.0.123 \
        -h new.example.com \
        new-machine

Start the VM.

    $ sudo virsh start new-machine

Then, new-machine is available by using new ip-address!

You can confirm new configuration.

    $ sudo ./virt-config.py -c new-machine
    ipaddr: 192.168.0.123
    hostname: new

## Supported OSs as Guest

+ Ubuntu
+ CentOS
