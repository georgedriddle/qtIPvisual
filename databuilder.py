from ipaddress import ip_network


def buildDisplayList(cidr: ip_network, startPrefix: int, endPrefix: int):
            ''' Returns a list of list, each being a subnet column '''
            e = []
            columnCount = 2 ** (endPrefix - startPrefix)
            print(f'should be {columnCount} columns')
            for prefix in list(range(startPrefix, endPrefix + 1)):
                # Begin making row data.
                e1 = []
                if prefix > cidr.prefixlen:
                    sbnet = list(cidr.subnets(new_prefix=prefix))
                    e1.extend(sbnet)
        
                elif prefix == cidr.prefixlen:
                    e1.extend([ip_network(cidr.with_prefixlen)])
        
                elif prefix < cidr.prefixlen:
                    e1.extend([cidr.supernet(new_prefix=prefix)])
                # End of Row Data
        
                newrow = ([{'cidr': x.with_prefixlen} for x in e1])
                e.append(newrow)
            return e
            # Need to add in a list comprehension to prepend each row to row  count
            #[l1.insert(0,"x") for n in range(32-1)]

network = ip_network("192.168.1.0/24")
start = 24
end = 32
data = buildDisplayList(network, start, end)
for row in data:
    print(row)