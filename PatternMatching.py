names = [('george','riddle'), ('rita'), ('thomas', 'Kennedy'), ('brittany', 'riddle'),
 ('angela', 'kennedy'), ('jessica', 'riddle'), ('jessica', 'trujillo'),
 ('chris', 'riddle')]

for name in names:
    match name:
        case 'george', _:
            print(f'{name} is king of the castle')
        case 'rita':
            print(f'{name} is queen of the castle')
        case 'tj':
            print(f'{name} is King of another castle')
        case _:
            print(f'{name} is a subject')
