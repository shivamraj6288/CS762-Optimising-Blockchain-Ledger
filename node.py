# from asyncio.windows_events import NULL
import copy

# from numpy.core.numeric import tensordot 
# from block import Block, RegBlock
from block import *
from transaction import Transaction
from event import *
# import heapq 
import numpy as np 
from random import sample
from utils import *
# from block import Blockchain
from params import *
from queue import pushq

num_acc_bal_per_block=NUM_ACC_BAL_PER_BLOCK
max_length_blockchain=MAX_LENGTH_BLOCKCHAIN
mining_feee=MINING_FEE
empty_blocks_length = EMPTY_BLOCKS_LENGTH

nodes = None 

class Node:
     

    def __init__(self, nid, speed, genesis, miningTime):
        self.nid = nid # unique id of all thr nodes 
        self.speed = speed # 1=fast, 0=slow
        self.blockchain = Blockchain(genesis)
        self.miningTime = miningTime # represent the mining power of node, mean mining time of node
        self.peer = set() # neighbours of the node
        self.txnReceived = set() # txn received till now 
        self.blockReceived = set() # blocks received till now 
        self.regenesis_status=False
        self.accounts=set()
        self.regBlockRecv=set()

        self.regenesisTime=[]
        self.size_of_blockchain = []

        self.waiting_to_merge =False 
        self.last_reg_block = None 
        self.new_blocks=set()
        self.empty_block_depth = 0 
        self.empty_block_mining = False 
        self.longest_chain_length = 0 
        self.startRegTime = None 
        self.endRegTime = None 
        


    def __str__ (self):
        return f"[Id:{pretty(self.nid, 5)}, Balance:{pretty(self.blockchain.balance(self.nid), 10)}]"

    # to establish connection between two node
    def addPeer(self,node):
        self.peer.add(node) 

    # this function is called if a new transaction is generated by the node 
    def txnSend(self, event):
        if self.blockchain.balance(self.nid) <= 0:
            return
        
        event.txn.value = np.random.randint(1, self.blockchain.balance(self.nid)+1)
        self.txnReceived.add(event.txn)

        for a in self.peer:
            t = event.time + computeLatency(self,a,1)
            action = TxnRecv(time=t, sender=self, receiver=a, txn=event.txn)
            pushq(action)

    # this function is called if the node recevies information about a transaction from its neighbours
    def txnRecv(self,event):
        if event.txn in self.txnReceived:
            return 
        self.txnReceived.add(event.txn)

        for a in self.peer:
            t = event.time + computeLatency(self,a,1)
            action = TxnRecv(time=t, sender=self.nid, receiver=a, txn=event.txn)
            pushq(action)

    def recordChainSize(self, time):
        self.size_of_blockchain.append((len(self.blockchain.blocks), time))
    # this function is called if node wants to mine a new block with given parent block
    def mineNewBlock(self, pblock, start_time):
        if (self.empty_block_mining):
            return 
        remaingTxn = self.txnReceived.difference(pblock.txnPool)
        txnToInclude = set(sample(remaingTxn, min(900,len(remaingTxn))))
        toBeDeleted = set()
        #print("debug p", pblock.balance)
        tmp_balance = pblock.balance.copy()
        for a in txnToInclude:
            if a.value > tmp_balance[a.sender.nid]:
                toBeDeleted.add(a)
            else:
                tmp_balance[a.sender.nid] -= a.value
                tmp_balance[a.receiver.nid] += a.value
        #print("debug", tmp_balance)
        txnToInclude = txnToInclude.difference(toBeDeleted)

        txnId = np.random.randint(0,2**31-1)
        coinBaseTxn = Transaction(tid=txnId, sender=-1, receiver=self, value=mining_feee)
        txnToInclude.add(coinBaseTxn)

        newBlockId = np.random.randint(0,2**31-1)
        newBlock = None
        if self.waiting_to_merge:
            newBlock = Block(bid=newBlockId, pbid=pblock, txnIncluded=txnToInclude, miner=self, regPbid=self.last_reg_block)
        else :
            newBlock = Block(bid=newBlockId, pbid=pblock, txnIncluded=txnToInclude, miner=self)
        assert newBlock.is_valid, "There is no point mining invalid blocks"
        mining_time = start_time + np.random.exponential(self.miningTime)
        newMiningEvent = BlockMined(time=mining_time, block=newBlock)
        pushq(newMiningEvent)
    
    def startMerging(self, start_time):
        self.waiting_to_merge = True 
        all_blocks_bid = set(self.blockchain.blocks.keys())
        blocks_to_delete = all_blocks_bid.difference(self.new_blocks)
        for bid in blocks_to_delete:
            if bid not in self.new_blocks:
                self.blockchain.blocks.pop(bid)
        
        self.mineNewBlock(pblock=self.blockchain.head,start_time=start_time)

        
            
        
            




    def mineRegBlock(self,block, start_time):
        remaining_accounts = self.accounts.difference(block.accIncluded)
        debug(f"remaining:- {len(remaining_accounts)}")
        debug(block)
        # debug(remaining_accounts)
        if len(remaining_accounts)<=0:
            self.regenesis_status=False
            self.endRegTime=start_time
            # debug ((self.startRegTime, 'qqqqqqqqqqqqqqqqqqqqqqqqqq'*10))
            # self.regenesisTime.append(self.endRegTime-self.startRegTime)
            self.last_reg_block = block 
            self.startMerging(start_time)
              
            
            return 
        accounts_to_include=set(sample(remaining_accounts,min(num_acc_bal_per_block,len(remaining_accounts))))
        txns=set()
        # accountsIds=set()
        for acc in accounts_to_include:
            txns.add(Transaction(tid=np.random.randint(0, 2**31-1),sender=-1,receiver=nodes[acc[0]],value=acc[1]))
            # accountsIds.add(acc[0])
        # self.accounts=self.accounts.difference(accounts_to_include)
        txnId = np.random.randint(0,2**31-1)
        coinBaseTxn = Transaction(tid=txnId, sender=-1, receiver=self, value=mining_feee)
        txns.add(coinBaseTxn)

        newBlockId = np.random.randint(0,2**31-1)
        newRegBlock= RegBlock(bid=newBlockId,pbid=block,txnIncluded=txns,miner=self,accIncluded=accounts_to_include)
        mining_time=start_time+(np.random.exponential(self.miningTime)/50)
        newRegMiningEvent = RegBlockMined(time=mining_time,block=newRegBlock)
        pushq(newRegMiningEvent)
    

    def startReGenesisPhase2(self,block,start_time):
        self.lastBlock = block 
        self.regenesis_status=True
        self.startRegTime=start_time
        # debug ("fffffffffffffffffffff"*10)
        debug ((self.startRegTime, start_time))
        
        # self.accounts=copy(block.balance)
        self.accounts=set(enumerate(block.balance))
        accounts_to_include=set(sample(self.accounts,min(num_acc_bal_per_block,len(self.accounts))))
        txns=set()
        # accountsIds = set()
        for acc in accounts_to_include:
            txns.add(Transaction(tid=np.random.randint(0, 2**31-1),sender=-1,receiver=nodes[acc[0]],value=acc[1]))
            # accountsIds.add(acc[0])
        txnId = np.random.randint(0,2**31-1)
        coinBaseTxn = Transaction(tid=txnId, sender=-1, receiver=self, value=mining_feee)
        txns.add(coinBaseTxn)
        # self.accounts=self.accounts.difference(accounts_to_include)
        newBlockId = np.random.randint(0,2**31-1)
        newRegBlock= RegBlock(bid=newBlockId,pbid=block,txnIncluded=txns,miner=self,accIncluded=accounts_to_include, first=True)
        mining_time=start_time+(np.random.exponential(self.miningTime)/50)
        newRegMiningEvent = RegBlockMined(time=mining_time,block=newRegBlock)
        pushq(newRegMiningEvent)
        

    def mineEmptyBlock(self,block,start_time):
        if self.empty_block_depth >= empty_blocks_length:
            self.empty_block_depth = 0 
            self.empty_block_mining = False 
            self.startReGenesisPhase2(block=block, start_time = start_time)
            self.mineNewBlock(pblock = block, start_time=start_time)
            return 
        txnId = np.random.randint(0,2**31-1)
        coinBaseTxn = Transaction(tid=txnId, sender=-1, receiver=self, value=mining_feee)
        txns = set () 
        txns.add(coinBaseTxn)
        newBlockId = np.random.randint(0,2**31-1)
        newBlock = Block(bid=newBlockId, pbid=block, txnIncluded=txns, miner=self)
        mining_time = start_time + np.random.exponential(self.miningTime)
        newMiningEvent = EmptyBlockMined(time=mining_time, block=newBlock)
        pushq(newMiningEvent)

    def startReGenesis(self,block,start_time):
        self.empty_block_mining = True 
        self.longest_chain_length = 0
        txnId = np.random.randint(0,2**31-1)
        coinBaseTxn = Transaction(tid=txnId, sender=-1, receiver=self, value=mining_feee)
        txns = set () 
        txns.add(coinBaseTxn)
        newBlockId = np.random.randint(0,2**31-1)
        newBlock = Block(bid=newBlockId, pbid=block, txnIncluded=txns, miner=self)
        mining_time = start_time + np.random.exponential(self.miningTime)
        newMiningEvent = EmptyBlockMined(time=mining_time, block=newBlock)
        pushq(newMiningEvent)

    
    def verifyAndAddReceivedEmptyBlock(self, event):
        self.blockReceived.add(event.block.bid)
        if event.block.bid in self.blockReceived:
            return 
        # debug(event.block)
        is_longest = self.blockchain.add_block(event.block, event.time)

        self.recordChainSize(event.time)

        if (is_longest):
            self.empty_block_depth+=1
            if self.empty_block_depth >= empty_blocks_length:
                self.empty_block_depth = 0 
                self.empty_block_mining = False 
                self.startReGenesisPhase2(block=event.block, start_time = event.time)
                self.mineNewBlock(block = event.block, start_time=event.time)
            else:
                self.mineEmptyBlock(block = event.block, start_time=event.time)

        for a in self.peer:
            lat = computeLatency(i=self, j=a, m=100+len(event.block.txnIncluded))
            action = EmptyBlockRecv(time=event.time+lat, sender=self, receiver=a, block=event.block)
            pushq(action)
    
    def recvSelfMinedEmptyBlock(self,event):
        self.blockReceived.add(event.block.bid)
        
        is_longest = self.blockchain.add_block(event.block, event.time)

        self.recordChainSize(event.time)
        
        if (is_longest):
            debug(event.block)
            self.empty_block_depth+=1
            if self.empty_block_depth >= empty_blocks_length:
                self.empty_block_depth = 0 
                self.empty_block_mining = False 
                self.startReGenesisPhase2(block=event.block, start_time = event.time)
                self.mineNewBlock(pblock = event.block, start_time=event.time)
            else:
                self.mineEmptyBlock(block = event.block, start_time=event.time)

        for a in self.peer:
            lat = computeLatency(i=self, j=a, m=100+len(event.block.txnIncluded))
            action = EmptyBlockRecv(time=event.time+lat, sender=self, receiver=a, block=event.block)
            pushq(action)
    
    
    
        
    
    def receiveSelfMinedRegBlock(self,event):
        self.regBlockRecv.add(event.block.bid)
        
        self.new_blocks.add(event.block.bid)
        is_long_reg = self.blockchain.add_reg_block(block=event.block, time=event.time)

        self.recordChainSize(event.time)

        if is_long_reg: 
            debug(event.block)
            for a in self.peer:
                lat = computeLatency(i=self, j=a, m=100+len(event.block.txnIncluded))
                action = RegBlockRecv(time=event.time+lat, sender=self, receiver=a, block=event.block)
                pushq(action)
            self.mineRegBlock(block=event.block,start_time=event.time)
            return True 
        
        return False 
    
    def verifyAndAddReceivedRegBlock(self,event):
        if event.block.bid in self.regBlockRecv:
            return 
        # debug(event.block)
        self.regBlockRecv.add(event.block.bid)
        self.new_blocks.add(event.block.bid)
        if not event.block.is_valid: # we do not propogate invalid blocks
            return
        is_longest = self.blockchain.add_reg_block(event.block, event.time)

        self.recordChainSize(event.time)

        if is_longest:
            self.mineRegBlock(block=event.block, start_time=event.time)

        for a in self.peer:
                lat = computeLatency(i=self, j=a, m=100+len(event.block.txnIncluded))
                action = RegBlockRecv(time=event.time+lat, sender=self, receiver=a, block=event.block)
                pushq(action)





        




    # this function is called, if node receives a block from its peers
    # block is verified and if the block is without any errors then its is added to blockchain 
    # and then transmitted to neighbours 
    # If addition of that block creates a primary chain then mining is started over that block
    def verifyAndAddReceivedBlock(self,event):
        if event.block.bid in self.blockReceived:
            return 
        self.blockReceived.add(event.block.bid)
        # debug(event.block)
        if self.waiting_to_merge:
            if event.block.regPbid == None:
                return 
            if event.block.regPbid.bid == self.last_reg_block.bid:
                self.waiting_to_merge=False
                self.last_reg_block = None 
            else:
                return 
        if(self.regenesis_status):
            self.new_blocks.add(event.block.bid)

        if not event.block.is_valid: # we do not propogate invalid blocks
            return
        
        is_longest = self.blockchain.add_block(event.block, event.time)

        self.recordChainSize(event.time)

        if is_longest:
            self.longest_chain_length+=1
            if len(self.blockchain.blocks)>=max_length_blockchain and self.empty_block_mining==False:
                self.startReGenesis(block=event.block,start_time=event.time)
            
                    
            self.mineNewBlock(pblock=event.block, start_time=event.time)
        
        for a in self.peer:
            lat = computeLatency(i=self,j=a,m=100+len(event.block.txnIncluded))
            action = BlockRecv(time=event.time + lat, sender=self, receiver=a, block=event.block)
            pushq(action)
    
    # this function is called once the mining of a block is completed, 
    # If after mining the addition of block creates a primary chain then
    # the block is shared with neighbours and mining is continued otherwise 
    # node waits a block whose addition will, create primary chain
    def receiveSelfMinedBlock(self, event):
        self.blockReceived.add(event.block.bid)
        
        if self.waiting_to_merge:
            if event.block.regPbid == None:
                return 
            if event.block.regPbid.bid == self.last_reg_block.bid:
                self.waiting_to_merge=False
                self.last_reg_block = None 
            else:
                return 
        
        is_longest = self.blockchain.add_block(event.block, event.time)

        self.recordChainSize(event.time)
        
        if (self.regenesis_status):
            self.new_blocks.add(event.block.bid)

        

        rv = 0

        if is_longest:
            debug(event.block)
            self.longest_chain_length+=1
            if len(self.blockchain.blocks)>=max_length_blockchain and self.empty_block_mining==False:
                self.startReGenesis(block=event.block,start_time=event.time)
            # print(f"{event.block}, Time:{pretty(event.time,10)}")
            
            rv = 1
            for a in self.peer:
                lat = computeLatency(i=self, j=a, m=100+len(event.block.txnIncluded))
                action = BlockRecv(time=event.time+lat, sender=self, receiver=a, block=event.block)
                pushq(action)
            self.mineNewBlock(pblock=event.block, start_time=event.time)
        
        return rv
    


def create_nodes(no_nodes, slow, ttmine):
    no_slow = int(slow*(no_nodes))
    gblock = Block(pbid=0, bid=1, txnIncluded=set(), miner=-1)
    gblock.balance = [0]*no_nodes
    global nodes 
    nodes = [
            Node(nid=i, speed=0, genesis=gblock, miningTime=ttmine[i])
            for i in range(no_slow)
        ] + [
            Node(nid=i, speed=1, genesis=gblock, miningTime=ttmine[i])
            for i in range(no_slow, no_nodes)
        ]