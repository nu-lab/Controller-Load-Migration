import psutil

if __name__=="__main__":
    ifaces = []
    output = ""
    ifconfig_data = psutil.net_if_addrs()
    for addr in ifconfig_data.keys():
        if addr != 'lo':
            ifaces.append(addr)
    for iface in ifaces:
        mac0 = ifconfig_data[iface][-1].address
        output += iface + " " + mac0 +" "
    print(output.strip())

        