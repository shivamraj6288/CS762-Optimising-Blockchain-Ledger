import copy
from operator import is_ 
from utils import *
from params import *
import networkx as nx


# This data structure contains all the details of a single block and the blockchain

class Blockchain:
    def __init__(self, gblock):
        self.blocks = {gblock.bid : (gblock, 0)}
        self.head = gblock
        self.g = nx.DiGraph()
        self.regHead=None
    
    def add_block(self, block, time):
        block.time=time 
        self.blocks[block.bid] = (block, time) 

        if(block.length >= self.head.length):
            for blk, _ in self.blocks.values():
                if(blk.bid == block.pbid.bid):
                    self.g.add_edge(block.bid, block.pbid.bid)
                if(blk.pbid != 0 and blk.pbid.bid == block.bid):
                    self.g.add_edge(blk.bid, block.bid)

            # cur = block
            # while(cur != 0 and cur in ):
            #     try:
            #         if(cur.bid in self.g.neighbors(cur.pbid.bid)):
            #             break
            #     except: pass
            #     if(cur.pbid != 0):
            #         self.g.add_edge(cur.bid, cur.pbid.bid)
            #     cur = cur.pbid

        if(block.length > self.head.length):
            self.head = block
            return True
        return False  

    def add_reg_block(self,block,time):
        block.time=time 
        self.blocks[block.bid]=(block,time)

        is_long = False
        if self.regHead==None:
            self.regHead=block
            is_long = True 
        elif self.regHead.length < block.length :
            self.regHead=block 
            is_long = True 
        for blk, _ in self.blocks.values():
            if(blk.bid == block.pbid.bid):
                self.g.add_edge(block.bid, block.pbid.bid)
            if(blk.pbid != 0 and blk.pbid.bid == block.bid):
                self.g.add_edge(blk.bid, block.bid)

        
        if is_long:
            for blk, _ in self.blocks.values():
                if(blk.bid == block.pbid.bid):
                    self.g.add_edge(block.bid, block.pbid.bid)
                if(blk.pbid != 0 and blk.pbid.bid == block.bid):
                    self.g.add_edge(blk.bid, block.bid)
            return True 

        return False 
        




    def balance(self, nid):
        return self.head.balance[nid]

    def __str__(self):
        for a in self.blocks.values():
            print(a)
        return ("Blocks Printed")

class Block:
    def __init__(self, bid, pbid, txnIncluded, miner, regPbid=None):
        self.bid = bid # block id
        self.pbid = pbid # parent block id
        self.txnIncluded = txnIncluded.copy()
        self.miner = miner
        self.regPbid=regPbid

        # txnPool stores all the txn mined till now 
        # length shows the length of chain from genesis block till current block 
        if pbid != 0:
            self.txnPool = pbid.txnPool
            self.length = pbid.length+1
        else:
            self.txnPool = set()
            self.length = 1
        
        if pbid != 0:
            self.balance = pbid.balance.copy()
        else:
            self.balance = [0]*NUM_NODES

        for a in self.txnIncluded: # updating balance of all the user 
            # debug(a.sender)
            if a.sender != -1:
                self.balance[a.sender.nid] -= a.value
            self.balance[a.receiver.nid] += a.value

        # no need to check parent  
        self.is_valid = True
        for a in self.txnIncluded:
            if a in self.txnPool:
                #print("debug a", a)
                self.is_valid = False
        for b in self.balance:
            if(b < 0):
                #print("debug b", self.balance)
                self.is_valid = False

        for a in self.txnIncluded:
            self.txnPool.add(a)
            
    def __str__ (self):
        if self.pbid!=0:
            return f"Id:{pretty(self.bid)}, Parent:{pretty(self.pbid.bid)}, Miner: {self.miner}, Txns:{pretty(len(self.txnIncluded), 5)}"
        else :
            return f"Id:{pretty(self.bid)}, Parent:{pretty(-1)}, Miner: {self.miner}, Txns:{pretty(len(self.txnIncluded), 5)}"


class RegBlock(Block):
    def __init__(self, bid, pbid, txnIncluded, miner, accIncluded, first=False):
        # first will tell whether this is first regensis block or not, which will help to decide wether to copy from previous bock or not 
        # accIncluded stores all the accounts whose balance is stored in this regenesis
        self.accIncluded=set()
        if not first:
            for a in pbid.accIncluded:
                self.accIncluded.add(a)
            # self.accIncluded=copy.deepcopy(pbid.accIncluded)
        for a in accIncluded:
            self.accIncluded.add(a)
        
        

        self.accIncluded=accIncluded
        super().__init__(bid=bid, pbid=pbid, txnIncluded=txnIncluded, miner=miner)

    def __str__ (self):
        if self.pbid!=0:
            return f"Id:{pretty(self.bid)}, Parent:{pretty(self.pbid.bid)}, Miner: {self.miner}, Accounts:{pretty(len(self.accIncluded), 5)}"
        else :
            return f"Id:{pretty(self.bid)}, Type: RegBlock Parent:{pretty(-1)}, Miner: {self.miner}, Accounts:{pretty(len(self.accIncluded), 5)}"  