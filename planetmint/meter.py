from pyJoules.handler.csv_handler import CSVHandler
import random


filename = '/tmp/result'  + str( random.randint(0,1000) ) + '.csv'
csv_handler = CSVHandler(filename)

def create_handler():
    filename = '/tmp/result'  + str( random.randint(0,1000) ) + '.csv'
    csv_handler = CSVHandler(filename)
    

    
    