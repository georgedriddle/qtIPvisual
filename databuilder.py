from ipaddress import IPv4Network


def checkCidr(cidr: IPv4Network, startPrefix: int) -> IPv4Network:
    """Checks if the display start is less than the network prefix.
    It will update the network to the start prefix if so. Otherwise
    returns same network back.
    """
    if startPrefix < cidr.prefixlen:
        newnet = str(cidr.network_address)
        cidr = IPv4Network(newnet + "/" + str(startPrefix), strict=False)
    return cidr


def buildDisplayList(cidr: IPv4Network, startPrefix: int, endPrefix: int):
    """Returns a list of list, each being a subnet column"""
    cidr = checkCidr(cidr, startPrefix)
    columnCount = endPrefix - startPrefix + 1
    rowCount = 2 ** (endPrefix - cidr.prefixlen)
    data: list = [[{} for c in range(columnCount)] for r in range(rowCount)]
    colNum = 0

    for prefix in list(range(startPrefix, endPrefix + 1)):
        # Begin making row data.
        sbnet = list(cidr.subnets(new_prefix=prefix))
        rowNum = 0
        for net in sbnet:
            data[rowNum][colNum] = {
                "network": net.with_prefixlen,
                "spansize": 2 ** (endPrefix - prefix),
            }
            rowNum += 2 ** (endPrefix - prefix)
        colNum += 1
    return data


if __name__ == "__main__":
    network = IPv4Network("192.168.1.0/24")
    start = 23
    end = 26
    networks = buildDisplayList(network, start, end)
    #  for item in networks:
    #    print(item)
    columnCount = end - start + 1
    rowCount = 2 ** (end - network.prefixlen)
    for currentrow in range(0, rowCount):
        for currentcol in range(0, columnCount):
            if networks[currentrow][currentcol]:
                print(networks[currentrow][currentcol])
            else:
                print("!")
