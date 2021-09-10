from ipaddress import ip_network

def makeEmptygrid(cCount: int, rCount:int) -> list[list]:

    table = []
    for r in range(rCount):
        rowdata = []
        for c in range(cCount):
            rowdata.append({})
        table.append(rowdata)
    return table


def buildDisplayList(cidr: ip_network, startPrefix: int, endPrefix: int):
    ''' Returns a list of list, each being a subnet column '''
    columnCount =  endPrefix - startPrefix + 1
    rowCount = 2 ** (endPrefix - startPrefix)
    data = makeEmptygrid(columnCount,rowCount)
    colNum = 0
    for prefix in list(range(startPrefix, endPrefix + 1)):
        # Begin making row data.
        if prefix >= cidr.prefixlen:
            sbnet = list(cidr.subnets(new_prefix=prefix))
            rowNum = 0
            for net in sbnet:
                data[rowNum][colNum] = {'network': net.with_prefixlen,
                                        'spansize': 2 ** (endPrefix - prefix)}
                rowNum += 2 ** (endPrefix - prefix)
        elif prefix < cidr.prefixlen:
            rowNum = 0
            sbnet = cidr.supernet(new_prefix=prefix)
            for net in sbnet:
                network = ip_network(net)
                data[rowNum][colNum] = {'network': network.with_prefixlen,
                                        'spansize': 2 ** (endPrefix - prefix)}
                rowNum += 2 ** (endPrefix - prefix)
        
        colNum += 1
    return data


if __name__ == '__main__':
    network = ip_network("192.168.1.0/24")
    start = 24
    end = 27
    networks = buildDisplayList(network, start, end)
    for item in networks:
        print(item)
    columnCount =  end - start + 1
    rowCount = 2 ** (end - start)
    for currentrow in range(0,rowCount):
        for currentcol in range(0,columnCount):
            if networks[currentrow][currentcol]:
                print(networks[currentrow][currentcol])
            else:
                print('!')

    print('!' * 80)


