from ipaddress import ip_network

def makeEmptygrid(cCount: int, rCount:int) -> list[list]:
    ''' Returns a null grid as a list of lists'''
    table = []
    for r in range(rCount):
        rowdata = []
        for c in range(cCount):
            rowdata.append({})
        table.append(rowdata)
    return table

def checkCidr(cidr: ip_network, startPrefix: int) -> ip_network:
    ''' Checks if the display start is less than the network prefix.
        It will update the network to the start prefix if so. Otherwise 
        returns same network back.
    '''
    if startPrefix < cidr.prefixlen:
        newnet = str(cidr.network_address)
        cidr = ip_network(newnet + '/' + str(startPrefix), strict=False)
    return cidr


def buildDisplayList(cidr: ip_network, startPrefix: int, endPrefix: int):
    ''' Returns a list of list, each being a subnet column '''
    cidr = checkCidr(cidr, startPrefix)
    columnCount =  endPrefix - startPrefix + 1
    rowCount = 2 ** (endPrefix - cidr.prefixlen)
    data = makeEmptygrid(columnCount,rowCount)
    colNum = 0
    
    for prefix in list(range(startPrefix, endPrefix + 1)):
        # Begin making row data.
        sbnet = list(cidr.subnets(new_prefix=prefix))
        rowNum = 0
        for net in sbnet:
            data[rowNum][colNum] = {'network': net.with_prefixlen,
                                    'spansize': 2 ** (endPrefix - prefix)}
            rowNum += (2 ** (endPrefix - prefix))
        colNum += 1
    return data


if __name__ == '__main__':
    network = ip_network("192.168.1.0/24")
    start = 23
    end = 26
    networks = buildDisplayList(network, start, end)
    #for item in networks:
    #    print(item)
    columnCount =  end - start + 1
    rowCount = 2 ** (end - network.prefixlen)
    for currentrow in range(0,rowCount):
        for currentcol in range(0,columnCount):
            if networks[currentrow][currentcol]:
                print(networks[currentrow][currentcol])
            else:
                print('!')


