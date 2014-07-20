from enum import Enum 

class Animations(Enum):
    LINEAR_L2R                  = 1
    LINEAR_R2L                  = 2
    MIDDLE_ALL_FROM_MIDDLE      = 3
    MIDDLE_ALL_TO_MIDDLE        = 4
    FIELDS_FROM_MIDDLE          = 5
    FIELDS_TO_MIDDLE            = 6
    FIELDS_L2R                  = 7
    FIELDS_R2L                  = 8
    
def getAnimationName(anim):
    
    strarr = str(anim).split('Animations.')
    return strarr[1]
    
 

class FieldColoringTypes(Enum):
    SINGLE  = 1
    TWO     = 2
    MULTI   = 3


class TimeSignatures(Enum):
    _4_4        =   0
    _3_4        =   1
    _6_8        =   2
    _5_4        =   3
    
    _3_8        =   4
    _5_8        =   5
    
    _9_8        =   6
    
def getTSString(index):
    
    numbers = []
    for s in (str(TimeSignatures(index))).split('_') :
        try :
            numbers.append(int(s))
        except ValueError : 
            pass
    
    return str(numbers[0]) + '/' + str(numbers[1])
        

