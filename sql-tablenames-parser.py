# -*- coding: utf-8 -*- 

import re

# 以下全是为了从sql中获取表(全部转化为小写)

NO_INDEX = -1
SPACE = " "
REGEX_SPACE = "\\s+"

TOKEN_ORACLE_HINT_START = "/\*+"
TOKEN_ORACLE_HINT_END = "\*/"
TOKEN_SINGLE_LINE_COMMENT = "--"
TOKEN_NEWLINE = "\\r\\n|\\r|\\n|\\n\\r"
TOKEN_SEMI_COLON = ";"
TOKEN_PARAN_START = "("
TOKEN_COMMA = ","
TOKEN_SET = "set"
TOKEN_OF = "of"
TOKEN_DUAL = "dual"
TOKEN_DELETE = "delete"
TOKEN_CREATE = "create"
TOKEN_INDEX = "index"
TOKEN_ASTERICK = "*"

KEYWORD_JOIN = "join"
KEYWORD_INTO = "into"
KEYWORD_TABLE = "table"
KEYWORD_FROM = "from"
KEYWORD_USING = "using"
KEYWORD_UPDATE = "update"

concerned = [KEYWORD_TABLE, KEYWORD_INTO, KEYWORD_JOIN, KEYWORD_USING, KEYWORD_UPDATE]
ignored = [TOKEN_PARAN_START, TOKEN_SET, TOKEN_OF, TOKEN_DUAL]

tables = {}

def indexOfRegex(regex, string):
    search = re.search(regex, string)
    if search:
        return search.start(), search.end()
    else:
        return -1,-1
    
def removeComments(sql):
    nextCommentPosition = -1
    commentSearch = re.search(TOKEN_ORACLE_HINT_START, sql)
    if commentSearch:
            nextCommentPosition = commentSearch.start()
    
    while nextCommentPosition > -1:
        newSql = sql[nextCommentPosition:]
        start,end = indexOfRegex(TOKEN_ORACLE_HINT_END, newSql)
        if end == -1:
            sql = sql[:nextCommentPosition]
        else:
            sql = sql[:nextCommentPosition] + sql[(nextCommentPosition+end):]
        
        commentSearch = re.search(TOKEN_ORACLE_HINT_START, sql)
        if commentSearch:
            nextCommentPosition = commentSearch.start()
        else:
            nextCommentPosition = -1
            
    return sql

def normalized(sql):
    normalized = sql.strip(" ").replace(TOKEN_COMMA, " , ").replace("(", " ( ").replace(")", " ) ")
    if len(normalized) > 0 and normalized[len(normalized)-1]==";":
        normalized=normalized[:len(normalized)-1]
    return normalized

def moreTokens(tokens, index):
    return index < len(tokens)

def isOracleSpecialDelete(token, tokens, index):
    index += 1
    if TOKEN_DELETE == token.lower():
        if moreTokens(tokens, index):
            nextToken = tokens[index]
            index += 1
            if KEYWORD_FROM != nextToken.lower() and TOKEN_ASTERICK != nextToken.lower():
                return True
    return False

def considerInclusion(token):
    global tables
    if token.lower() not in ignored and not tables.has_key(token.lower()):
        tables[token.lower()] = token
        
def handleSpecialOracleSpecialDelete(currentToken, tokens, index):
    tableName = tokens[index + 1]
    considerInclusion(tableName)
    
def hasIthToken(tokens, currentIndex, tokenNumber):
    if moreTokens(tokens, currentIndex) and len(tokens) > currentIndex + tokenNumber:
        return True
    return False

def isCreateIndex(currentToken, tokens, index):
    index += 1;
    if TOKEN_CREATE == currentToken.lower() and hasIthToken(tokens, index, 3):
        nextToken = tokens[index]
        index += 1
        if TOKEN_INDEX.equals(nextToken.lower()):
            return True
    return False

def handleCreateIndex(currentToken, tokens, index):
    tableName = tokens[index + 4]
    considerInclusion(tableName)
    
def isFromToken(currentToken):
    return KEYWORD_FROM == currentToken.lower()

def shouldProcessMultipleTables(nextToken):
        return nextToken != "" and nextToken == TOKEN_COMMA;
    
def processNonAliasedMultiTables(tokens, index, nextToken):
        while nextToken == TOKEN_COMMA:
            currentToken = tokens[index]
            index += 1
            considerInclusion(currentToken)
            if moreTokens(tokens, index):
                nextToken = tokens[index]
                index += 1
            else:
                break
                
def processAliasedMultiTables(tokens, index, currentToken):
    nextNextToken = ""
    if moreTokens(tokens, index):
        nextNextToken = tokens[index]
        index+=1
        
    if shouldProcessMultipleTables(nextNextToken):
        while moreTokens(tokens, index) and nextNextToken == TOKEN_COMMA:
            if moreTokens(tokens, index):
                currentToken = tokens[index]
                index+=1
            if moreTokens(tokens, index):
                index+=1
            if moreTokens(tokens, index):
                nextNextToken = tokens[index]
                index+=1
            considerInclusion(currentToken)

def processFromToken(tokens, index):
    currentToken = tokens[index]
    index += 1
    considerInclusion(currentToken)
    
    nextToken = ""
    if moreTokens(tokens, index):
        nextToken = tokens[index]
        index+=1
    
    if shouldProcessMultipleTables(nextToken):
        processNonAliasedMultiTables(tokens, index, nextToken)
    else:
        processAliasedMultiTables(tokens, index, currentToken)
        
def shouldProcess(currentToken): 
    return currentToken.lower() in concerned

def parseTableNames(sql):
    global tables
    tables = {}
    nocomments = removeComments(sql)
    normalizedSql = normalized(nocomments)
    pretokens = normalizedSql.split(" ")
    tokens = []
    for token in pretokens:
        if token != "" and token.strip(" ") != "":
            tokens.append(token)
    
    
    if (len(tokens) == 0):
        return set()
    
    index = 0
    firstToken = tokens[index]
    
    if isOracleSpecialDelete(firstToken, tokens, index):
        handleSpecialOracleSpecialDelete(firstToken, tokens, index)
    elif isCreateIndex(firstToken, tokens, index):
        handleCreateIndex(firstToken, tokens, index)
    else:
        while moreTokens(tokens, index):
            currentToken = tokens[index]
            index += 1
            
            if isFromToken(currentToken):
                processFromToken(tokens, index)
            elif shouldProcess(currentToken):
                nextToken = tokens[index]
                index+=1
                considerInclusion(nextToken)
                
                if moreTokens(tokens, index):
                    nextToken = tokens[index]
                    index+=1
    
    return tables.keys()


print parseTableNames("SELECT         b.ID as ID, b.BrandName as BrandName, b.Logo as Logo, b.Hot as Hot, b.Country as Country, b.QualityLevel as QualityLevel, b.AddTime as AddTime, b.UpdateTime as UpdateTime         FROM ShopBrandCategory as sbc         LEFT JOIN MarketShop as s on sbc.shopID = s.shopID         LEFT JOIN MarketCategory as c ON c.ID = sbc.CategoryID         LEFT JOIN MarketBrand as b ON b.ID = sbc.BrandID         WHERE s.MarketID = ?         AND c.ParentID = ?         ORDER BY b.Hot DESC")
