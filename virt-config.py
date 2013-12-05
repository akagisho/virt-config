#!/usr/bin/env python

import os
import sys
import getopt
import re
import libvirt
from xml.etree.ElementTree import *
import guestfs

class VirtEdit:
    def __init__(self, domname):
        supported_distros = ["ubuntu", "centos"]

        conn = libvirt.open("qemu:///system")
        self.conn = conn

        if not self.exists(domname):
            raise Exception("Domain not found: %s" % domname)
        domain = self.conn.lookupByName(domname)
        self.domain = domain

        if domain.isActive():
            raise Exception("Domain is running: %s" % domname)

        g = guestfs.GuestFS()
        g.add_domain(domname)
        g.launch()
        root = g.inspect_os()[0]
        distro = g.inspect_get_distro(root)

        if distro not in supported_distros:
            raise Exception("Unsupported OS: %s" % distro)

        g.mount(root, "/")
        self.g = g
        self.distro = distro

    def exists(self, domname): 
        for domain in self.conn.listDefinedDomains():
            if domain == domname:
                return True
        for domid in self.conn.listDomainsID():
            domain = self.conn.lookupByID(domid)
            if domain.name() == domname:
                return True
        return False

    def update_ipaddr(self, ipaddr):
        g = self.g
        distro = self.distro

        if distro == "ubuntu":
            filename = "/etc/network/interfaces"
            data = g.read_file(filename)
            regexp = re.compile(r'^(\s+address)\s+[\d\.]+')
            flag = False
            new_data = ""
            for line in data.split("\n"):
                m = regexp.match(line)
                if m:
                    flag = True
                    line = "%s %s" % (m.group(1), ipaddr)
                new_data += line + "\n"
            if flag:
                g.write(filename, new_data)
            else:
                raise Exception("Unsupported format: %s" % filename)
            g.write(filename, new_data)
        elif distro == "centos":
            filename = "/etc/sysconfig/network-scripts/ifcfg-eth0"
            data = g.read_file(filename)
            regexp1 = re.compile(r'^IPADDR=.*$')
            regexp2 = re.compile(r'^HWADDR=.*$')
            flag = False
            new_data = ""
            for line in data.split("\n"):
                if regexp1.match(line):
                    flag = True
                    line = "IPADDR=\"%s\"" % ipaddr
                elif regexp2.match(line):
                    line = "#" + line
                new_data += line + "\n"
            if flag:
                g.write(filename, new_data)
            else:
                raise Exception("Unsupported format: %s" % filename)

            filename = "/etc/udev/rules.d/70-persistent-net.rules"
            g.write(filename, "")

    def update_hostname(self, fqdn):
        g = self.g
        distro = self.distro

        if distro == "ubuntu":
            hostname = fqdn.rsplit(".", 2)[0]
            filename = "/etc/hostname"
            g.write(filename, hostname)
        elif distro == "centos":
            filename = "/etc/sysconfig/network"
            data = g.read_file(filename)
            regexp = re.compile(r'^HOSTNAME=.*$')
            flag = False
            new_data = ""
            for line in data.split("\n"):
                if regexp.match(line):
                    flag = True
                    line = "HOSTNAME=\"%s\"" % fqdn
                new_data += line + "\n"
            if flag:
                g.write(filename, new_data)
            else:
                raise Exception("Unsupported format: %s" % filename)

    def update_hosts(self, ipaddr, fqdn):
        g = self.g

        if (fqdn.count(".") > 0):
            hostname, domain = fqdn.split(".", 1)
            add_line = "{0}\t{1} {2}".format(ipaddr, hostname, fqdn)
        else:
            add_line = "{0}\t{1}".format(ipaddr, hostname)

        regexp = re.compile(r'^%s\s.*$' % ipaddr.replace(".", "\\."))

        filename = "/etc/hosts"
        data = g.read_file(filename)

        flag = False
        new_data = ""
        for line in data.split("\n"):
            if regexp.match(line):
                flag = True
                line = add_line
            new_data += line + "\n"
        if not flag:
            new_data += add_line

        g.write(filename, new_data)

    def print_config(self):
        g = self.g
        distro = self.distro

        ipaddr = "unknown"
        hostname = "unknown"

        if distro == "ubuntu":
            filename = "/etc/network/interfaces"
            if g.is_file(filename):
                regexp = re.compile(r'\s+address\s+([\d\.]+)$')
                data = g.read_file(filename)
                for line in data.split("\n"):
                    m = regexp.match(line)
                    if m:
                        ipaddr = m.group(1)

            filename = "/etc/hostname"
            if g.is_file(filename):
                hostname = g.read_file(filename).split("\n", 1)[0]

        elif distro == "centos":
            filename = "/etc/sysconfig/network-scripts/ifcfg-eth0"
            if g.is_file(filename):
                regexp = re.compile(r'^IPADDR=["\']?([^"\']*)["\']?$')
                data = g.read_file(filename)
                for line in data.split("\n"):
                    m = regexp.match(line)
                    if m:
                        ipaddr = m.group(1)

            filename = "/etc/sysconfig/network"
            if g.is_file(filename):
                regexp = re.compile(r'^HOSTNAME=["\']?([^"\']*)["\']?$')
                data = g.read_file(filename)
                for line in data.split("\n"):
                    m = regexp.match(line)
                    if m:
                        hostname = m.group(1)

        print "ipaddr: %s" % ipaddr
        print "hostname: %s" % hostname

def usage():
    print """\
Usage:
    {0} [options] domname
Options:
    -i new_ipaddr: update ip-address
    -h new_hostname update hostname
    -c: confirm result
""".format(os.path.basename(__file__))
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv, "[i:h:c]")
    except Exception as e:
        print str(e)
        usage()

    if len(args) <= 1:
        usage()

    ipaddr = None
    hostname = None
    confirm = False
    domname = args[1]

    for k, v in opts:
        if k == "-i":
            ipaddr = v
        if k == "-h":
            hostname = v
        if k == "-c":
            confirm = True

    if ipaddr and not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ipaddr):
        sys.exit("Invalid ip-address: " + ipaddr)
    if hostname and not re.match(r'^[a-zA-Z0-9\.\-_]+$', hostname):
        sys.exit("Invalid hostname: " + hostname)

    try:
        virtEdit = VirtEdit(domname)
    except Exception as e:
        sys.exit(str(e))

    if ipaddr:
        virtEdit.update_ipaddr(ipaddr)

    if hostname:
        virtEdit.update_hostname(hostname)

    if ipaddr and hostname:
        virtEdit.update_hosts(ipaddr, hostname)

    if confirm:
        virtEdit.print_config()

if __name__ == "__main__":
    main() 
