#!/usr/bin/env python3

# Found this code on GitHubGist and adjusted to the YAML-PDDL converter needs.
# Igor Tikhonin, 2018

"""
Grammar:
Expression --> AndTerm [or AndTerm]*
AndTerm --> Condition [and Condition]*
Condition --> Terminal >,<,>=,<=,==,!= Terminal | Terminal | not Terminal | (Expression) | not (Expression)
Terminal --> Number, String, or Variable

Usage:
from boolparser import *
p = BooleanParser('<expression text>')
"""

# not a and b or not (c and b)

class TokenType:
    NUM, STR, VAR, GT, GTE, LT, LTE, EQ, NEQ, LP, RP, AND, OR, NOT = range(14)

class Tokenizer:
    expression = None
    tokens = None
    tokenTypes = None
    i = 0

    def __init__(self, exp):
        self.expression = exp
        self.tokenize()

    def next(self):
        self.i += 1
        return self.tokens[self.i-1]

    def peek(self):
        return self.tokens[self.i]

    def hasNext(self):
        return self.i < len(self.tokens)

    def nextTokenType(self):
        return self.tokenTypes[self.i]

    def nextTokenTypeIsOperator(self):
        t = self.tokenTypes[self.i]
        return t == TokenType.GT or t == TokenType.GTE \
            or t == TokenType.LT or t == TokenType.LTE \
            or t == TokenType.EQ or t == TokenType.NEQ

    def tokenize(self):
        import re
        reg = re.compile(r'(\band\b|\bor\b|\bnot\b|!=|==|<=|>=|<|>|\(|\))')
        self.tokens = reg.split(self.expression)
        self.tokens = [t.strip() for t in self.tokens if t.strip() != '']

        self.tokenTypes = []
        for t in self.tokens:
            if t == 'and':
                self.tokenTypes.append(TokenType.AND)
            elif t == 'or':
                self.tokenTypes.append(TokenType.OR)
            elif t == 'not':
                self.tokenTypes.append(TokenType.NOT)
            elif t == '(':
                self.tokenTypes.append(TokenType.LP)
            elif t == ')':
                self.tokenTypes.append(TokenType.RP)
            elif t == '<':
                self.tokenTypes.append(TokenType.LT)
            elif t == '<=':
                self.tokenTypes.append(TokenType.LTE)
            elif t == '>':
                self.tokenTypes.append(TokenType.GT)
            elif t == '>=':
                self.tokenTypes.append(TokenType.GTE)
            elif t == '==':
                self.tokenTypes.append(TokenType.EQ)
            elif t == '!=':
                self.tokenTypes.append(TokenType.NEQ)
            else:
                # number or string, or variable
                if (t[0] == '"' and t[-1] == '"') or (t[0] == "'" and t[-1] == "'"):
                    self.tokenTypes.append(TokenType.STR)
                else:
                    try:
                        number = float(t)
                        self.tokenTypes.append(TokenType.NUM)
                    except:
                        if re.search('^[a-zA-Z_.]+$', t):
                            self.tokenTypes.append(TokenType.VAR)
                        else:
                            self.tokenTypes.append(None)

class BooleanParser:
    tokenizer = None
    root = None

    def __init__(self, exp):
        # exp is either string or Tokenizer type
        if isinstance(exp, str):
            self.tokenizer = Tokenizer(exp)
        else:
            self.tokenizer = exp
        self.parse()

    def parse(self):
        self.root = self.parseExpression()

    def parseExpression(self):
        andTerm1 = self.parseAndTerm()
        while self.tokenizer.hasNext() and self.tokenizer.nextTokenType() == TokenType.OR:
            self.tokenizer.next()
            andTermX = self.parseAndTerm()
            andTerm = dict(tokenType=TokenType.OR)
            andTerm['left'] = andTerm1
            andTerm['right'] = andTermX
            andTerm1 = andTerm
        return andTerm1

    def parseAndTerm(self):
        condition1 = self.parseCondition()
        while self.tokenizer.hasNext() and self.tokenizer.nextTokenType() == TokenType.AND:
            self.tokenizer.next()
            conditionX = self.parseCondition()
            condition = dict(tokenType=TokenType.AND)
            condition['left'] = condition1
            condition['right'] = conditionX
            condition1 = condition
        return condition1

    def parseNegation(self):
        negation = None
        if self.tokenizer.hasNext() and self.tokenizer.nextTokenType() == TokenType.NOT:
            negation = dict(tokenType=TokenType.NOT)
            self.tokenizer.next()
        return negation

    def parseCondition(self):
        negation = self.parseNegation()
        if not self.tokenizer.hasNext():
            raise Exception('Empty condition')
        if self.tokenizer.nextTokenType() == TokenType.LP:
            self.tokenizer.next()
            expression = self.parseExpression()
            if self.tokenizer.hasNext() and self.tokenizer.nextTokenType() == TokenType.RP:
                self.tokenizer.next()
                if negation != None:
                    negation['right'] = expression
                    return negation
                return expression
            else:
                raise Exception("Closing ) expected, but got " + self.tokenizer.next())
        else:
            terminal1 = self.parseTerminal()
            if self.tokenizer.hasNext() and self.tokenizer.nextTokenTypeIsOperator():
                condition = dict(tokenType=self.tokenizer.nextTokenType())
                self.tokenizer.next()
                terminal2 = self.parseTerminal()
                condition['left'] = terminal1
                condition['right'] = terminal2
                if negation != None:
                    negation['right'] = condition
                    condition = negation
                return condition
            else:
                if negation != None:
                    negation['right'] = terminal1
                    terminal1 = negation
            return terminal1

    def parseTerminal(self):
        if not self.tokenizer.hasNext():
            raise Exception('Empty terminal token')
        tokenType = self.tokenizer.nextTokenType()
        n = dict(tokenType=tokenType)
        if tokenType == TokenType.NUM:
            n['value'] = float(self.tokenizer.next())
        elif tokenType == TokenType.STR or tokenType == TokenType.VAR:
            n['value'] = self.tokenizer.next()
        else:
            raise Exception('NUM, STR, or VAR expected, but got ' + self.tokenizer.next())
        return n
