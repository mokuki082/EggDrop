duplicates = {}

with open('data/client.log', 'r') as f:
    for n, line in enumerate(f):
        if line in duplicates:
            duplicates[line].append(n)
        else:
            duplicates[line] = [n]

for i in sorted(duplicates, key=lambda x: (len(duplicates[x]), duplicates[x][0])):
    print("%{}s %s".format(30) % (i[:-1], duplicates[i]))
