def makeEmptygrid(cCount: int, rCount:int) -> list[list]:

    table = []
    for r in range(rCount):
        rowdata = []
        for c in range(cCount):
            rowdata.append('')
        table.append(rowdata)
    for row in table:
        print(row)
    return table

if __name__ == '__main__':
    makeEmptygrid(3,8)