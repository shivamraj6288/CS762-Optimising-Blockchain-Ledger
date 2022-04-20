# a:{}
# a['ahgs']:1
# a['jsh']:2
# a['jsgd']:3
# a['jghduh']:0
# a['oihiuh']:4
# for x in a.items():
#     print(x[0])
# x:set(a.items())
# # print(x)
# b: [11,12,13,14]
# x:set(enumerate (b))
# print (x)

c=set()
c.add(1)
c.add(2)
c.add(3)
for i in range(0,10):
    if i not in c:
        print(i)


# from transaction import Transaction
# c.add({"tid":11,"sender":112,"receiver":113,"value" :1111})
# c.add({"tid":12,"sender":113,"receiver":114,"value" :11})

# for a in c:
#     a.sender=1100000
# for a in c:
#     print (a)