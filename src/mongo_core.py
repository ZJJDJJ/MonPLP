#! /usr/bin/env python2.7
# coding=utf-8
__author__ = 'bulu_dog'

#import area
import datetime
from pymongo import MongoClient
from pymongo import ReturnDocument

'''
Mongo类
版本：2015/06/22
建立连接，主要用于获取指定数据库内特定的collection
'''
class Mongo(object):
    def __init__(self, name, host="localhost", port=27017):
        self.db = None
        self.name = name
        self.host = host
        self.port = port
        self.client = None
        self.initConnection(host, port)
        self.initDataBase()

    # get connection with MongoClient
    def initConnection(self, host="localhost", port=27017):
        self.client = MongoClient(host, port)
        #return self.client

    # get database with db name
    def initDataBase(self):
        self.db = self.client[self.name]

    #get collection by name
    def getCollection(self, cname):
        return self.db[cname]

    def close(self):
        self.client.close()

'''
term collection 代理类
版本：2015/06/22
term collection 建立索引情况：
(None)
'''
class TermCollection(object):
    def __init__(self):
        #init function
        self.name = "term"
        self.idTable = "idTable"
        self.mongo = Mongo("logic")         #获取Mongo类，连接数据库
        self.num = -1
        self.collection = self.mongo.getCollection(self.name)           #获取term 和 idTable 集合
        self.delCollection = self.mongo.getCollection(self.idTable)
        self.counter = self.collection.find_one({"term":"__counter"})   #验证term counter
        if (self.counter == None):
            #term counter 不存在则建立
            self.collection.insert_one({"term":"__counter",
                                        "num":0,
                                        "desc":"counter to make term collection'id inc automatically"})
        else:
            self.num = self.counter['num']
            print '---------Load [term] collection done, all %d documents---------' % self.num  #成功信息，显示当前term数

    def __insert_one(self, document):
        #检查id pool中是否有id，若有且小于当前num值，则取出作为id
        new_id = -1
        id_num = self.delCollection.count()
        if id_num > 0:
            new_id = self.delCollection.find_one_and_delete({'id':{ '$gte': 0 }})['id'] #取出new_id，并删除原记录
            document["id"] = new_id
        else:
            #inc 1 to the num counter
            self.counter = self.collection.find_one_and_update({"term":"__counter"},
                                                                {'$inc':{'num':1}},
                                                                return_document=ReturnDocument.AFTER)
            self.num = self.counter["num"]
            #set the term id
            document["id"] = self.num
        #insert the term document
        self.collection.insert_one(document)

    #删除一条记录
    def __delete_one(self, filter):
        try:
            del_doc = self.collection.find_one_and_delete(filter)
            id = del_doc['id']
            self.delCollection.save({'id':id})
            print "delete 1 document which contain {id:%d} successfully" % id
        except:
            print "[Error]delete error. Sure the doc in the term collection?"

    #修正数据库，目前并不需要
    def repair(self):
        #检查计数是否正确
        self.num = self.collection.find_one({"term":"__counter"})['num']
        del_num = self.delCollection.count()
        term_num = self.collection.count() - 1
        #term表中counter的num字段应该 = del掉的id数量 + 现有term数量
        if self.num != del_num + term_num:
            print "[Error] num wrong"
            # <备份现有数据，导入term_wrong表>
            self._reduce() #回退数据库，出现重大逻辑错误，后期这里添加
        else:   #若一致
            print "The term collection is all right"


    #关闭数据库连接，断开term集合的操作
    def close(self):
        self.mongo.client.close()

    #直接insert term，封装方法
    def insert_term(self, term):
        self.__insert_one({'term':term})

    #直接delete term，封装方法
    def delete_term(self, term):
        self.__delete_one({'term':term})

    #reduce
    #DEPRECATED - use [repair] to repair the term collection
    def _reduce(self):
        #回退数据库到无数据版本,除非调试，否则不推荐使用
        #删除term集合,重置counter
        self.collection.drop()
        self.collection.insert_one({"term":"__counter",
                                        "num":0,
                                        "desc":"counter to make term collection'id inc automatically"})
        #删除id表内容
        self.delCollection.drop()
        self.mongo.db.create_collection(self.idTable)
    #Class TermCollection Done!

class RelationCollection(object):
    def __init__(self):
        self.name = "relation"

#test
if __name__ == "__main__":
    term = TermCollection()
    term.close()