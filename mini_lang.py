# TOKEN
class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line
    def __repr__(self):
        return f"<{self.type}, {self.value}>"
# SCANNER (ANÁLISE LÉXICA)
KEYWORDS = {
    'var','def','if','else','while','return','print',
    'int','real','bool','void','true','false','and','or','not'
}
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1

    def peek(self, k=0):
        p = self.pos + k
        return self.text[p] if p < len(self.text) else None

    def advance(self):
        c = self.peek()
        self.pos += 1
        if c == '\n': self.line += 1
        return c

    def tokenize(self):
        tokens = []
        while self.peek():
            c = self.peek()
            if c.isspace():
                self.advance(); continue

            # números
            if c.isdigit():
                num = ''
                while self.peek() and self.peek().isdigit():
                    num += self.advance()
                tokens.append(Token('INT', num, self.line)); continue

            # identificadores e palavras-chave
            if c.isalpha() or c == '_':
                ident = ''
                while self.peek() and (self.peek().isalnum() or self.peek()=='_'):
                    ident += self.advance()
                t = ident.upper() if ident in KEYWORDS else 'ID'
                tokens.append(Token(t, ident, self.line)); continue

            # operadores compostos
            if c == '=' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token('EQ','==',self.line)); continue
            if c == '!' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token('NE','!=',self.line)); continue
            if c == '<' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token('LE','<=',self.line)); continue
            if c == '>' and self.peek(1) == '=':
                self.advance(); self.advance()
                tokens.append(Token('GE','>=',self.line)); continue

            # operadores simples e símbolos
            single = {
                '+':'PLUS','-':'MINUS','*':'MUL','/':'DIV',
                '(':'LPAREN',')':'RPAREN','{':'LBRACE','}':'RBRACE',
                ';':'SEMICOLON',':':'COLON',',':'COMMA',
                '=':'ASSIGN','<':'LT','>':'GT'
            }
            if c in single:
                tokens.append(Token(single[c], c, self.line))
                self.advance(); continue

            raise Exception(f"Caractere inválido '{c}' linha {self.line}")

        tokens.append(Token('EOF','',self.line))
        return tokens
# AST NODES
class Program: 
    def __init__(self, stmts): self.stmts = stmts
class VarDecl:
    def __init__(self,n,t,e): self.name=n; self.type=t; self.expr=e
class Assign:
    def __init__(self,n,e): self.name=n; self.expr=e
class Print:
    def __init__(self,e): self.expr=e
class If:
    def __init__(self,c,t,e=None): self.cond=c; self.then_block=t; self.else_block=e
class While:
    def __init__(self,c,b): self.cond=c; self.block=b
class Int:
    def __init__(self,v): self.value=v
class Bool:
    def __init__(self,v): self.value=v
class Var:
    def __init__(self,n): self.name=n
class BinOp:
    def __init__(self,l,o,r): self.left=l; self.op=o; self.right=r
# PARSER (DESCENDENTE RECURSIVO)
class Parser:
    def __init__(self,tokens): self.tokens=tokens; self.pos=0
    def cur(self): return self.tokens[self.pos]
    def eat(self,t):
        if self.cur().type==t: self.pos+=1
        else: raise Exception(f"Esperado {t} linha {self.cur().line}")

    def parse(self):
        stmts=[]
        while self.cur().type!='EOF': stmts.append(self.statement())
        return Program(stmts)

    def statement(self):
        if self.cur().type=='VAR': return self.var_decl()
        if self.cur().type=='ID': return self.assign()
        if self.cur().type=='PRINT': return self.print_stmt()
        if self.cur().type=='IF': return self.if_stmt()
        if self.cur().type=='WHILE': return self.while_stmt()
        raise Exception(f"Comando inválido linha {self.cur().line}")

    def block(self):
        stmts=[]
        self.eat('LBRACE')
        while self.cur().type!='RBRACE': stmts.append(self.statement())
        self.eat('RBRACE')
        return stmts

    def if_stmt(self):
        self.eat('IF'); self.eat('LPAREN')
        cond=self.expr(); self.eat('RPAREN')
        then_block=self.block(); else_block=None
        if self.cur().type=='ELSE':
            self.eat('ELSE'); else_block=self.block()
        return If(cond,then_block,else_block)

    def while_stmt(self):
        self.eat('WHILE'); self.eat('LPAREN')
        cond=self.expr(); self.eat('RPAREN')
        block=self.block(); return While(cond,block)

    def var_decl(self):
        self.eat('VAR'); name=self.cur().value; self.eat('ID')
        self.eat('COLON'); t=self.cur().value; self.eat(self.cur().type)
        self.eat('ASSIGN'); e=self.expr(); self.eat('SEMICOLON')
        return VarDecl(name,t,e)

    def assign(self):
        name=self.cur().value; self.eat('ID')
        self.eat('ASSIGN'); e=self.expr(); self.eat('SEMICOLON')
        return Assign(name,e)

    def print_stmt(self):
        self.eat('PRINT'); e=self.expr(); self.eat('SEMICOLON')
        return Print(e)

    def expr(self):
        node=self.simple_expr()
        if self.cur().type in ('LT','GT','EQ','NE','LE','GE'):
            op=self.cur().value; self.eat(self.cur().type)
            node=BinOp(node,op,self.simple_expr())
        return node

    def simple_expr(self):
        node=self.term()
        while self.cur().type in ('PLUS','MINUS'):
            op=self.cur().value; self.eat(self.cur().type)
            node=BinOp(node,op,self.term())
        return node

    def term(self):
        tok=self.cur()
        if tok.type=='INT': self.eat('INT'); return Int(tok.value)
        if tok.type in ('TRUE','FALSE'):
            self.eat(tok.type); return Bool(tok.value)
        if tok.type=='ID': self.eat('ID'); return Var(tok.value)
        raise Exception(f"Expressão inválida linha {tok.line}")
# SEMÂNTICO
class Semantic:
    def __init__(self): self.scopes=[{}]
    def push(self): self.scopes.append({})
    def pop(self): self.scopes.pop()
    def declare(self,n,t):
        if n in self.scopes[-1]: raise Exception("Variável duplicada")
        self.scopes[-1][n]=t
    def lookup(self,n):
        for s in reversed(self.scopes):
            if n in s: return s[n]
        raise Exception("Variável não declarada")

    def visit(self,node):
        if isinstance(node,Program):
            for s in node.stmts: self.visit(s)
        if isinstance(node,VarDecl):
            self.visit(node.expr); self.declare(node.name,node.type)
        if isinstance(node,Assign):
            self.lookup(node.name); self.visit(node.expr)
        if isinstance(node,Print): self.visit(node.expr)
        if isinstance(node,If):
            self.visit(node.cond); self.push()
            for s in node.then_block: self.visit(s)
            self.pop()
            if node.else_block:
                self.push()
                for s in node.else_block: self.visit(s)
                self.pop()
        if isinstance(node,While):
            self.visit(node.cond); self.push()
            for s in node.block: self.visit(s)
            self.pop()
        if isinstance(node,BinOp):
            self.visit(node.left); self.visit(node.right)
        if isinstance(node,(Int,Bool,Var)): return
# CODE GENERATOR (PYTHON)
class Generator:
    def gen_block(self,stmts,ind):
        return ''.join('    '*ind + self.gen(s)+'\n' for s in stmts)
    def gen(self,node):
        if isinstance(node,Program): return ''.join(self.gen(s)+'\n' for s in node.stmts)
        if isinstance(node,VarDecl): return f"{node.name} = {self.gen(node.expr)}"
        if isinstance(node,Assign): return f"{node.name} = {self.gen(node.expr)}"
        if isinstance(node,Print): return f"print({self.gen(node.expr)})"
        if isinstance(node,If):
            code=f"if {self.gen(node.cond)}:\n"
            code+=self.gen_block(node.then_block,1)
            if node.else_block:
                code+="else:\n"+self.gen_block(node.else_block,1)
            return code.rstrip()
        if isinstance(node,While):
            return f"while {self.gen(node.cond)}:\n"+self.gen_block(node.block,1).rstrip()
        if isinstance(node,Int): return node.value
        if isinstance(node,Bool): return 'True' if node.value=='true' else 'False'
        if isinstance(node,Var): return node.name
        if isinstance(node,BinOp): return f"({self.gen(node.left)} {node.op} {self.gen(node.right)})"
# MAIN
if __name__=='__main__':
    codigo=open('teste.ml').read()
    tokens=Lexer(codigo).tokenize()
    ast=Parser(tokens).parse()
    Semantic().visit(ast)
    py=Generator().gen(ast)
    open('saida.py','w').write(py)
    print('Código gerado com sucesso!')