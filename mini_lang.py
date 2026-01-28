import sys
# TOKEN
class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line
    def __repr__(self):
        return f"<{self.type}, {self.value}>"

# SCANNER
KEYWORDS = {
    'var','def','if','else','while','return','print',
    'int','real','bool','void','true','false','and','or','not'
}

class Lexer:
    def __init__(self, text):
        self.text, self.pos, self.line = text, 0, 1
    def peek(self, k=0):
        p = self.pos + k
        return self.text[p] if p < len(self.text) else None
    def advance(self):
        c = self.peek(); self.pos += 1
        if c == '\n': self.line += 1
        return c
    def tokenize(self):
        tokens=[]
        while self.peek():
            c=self.peek()
            if c.isspace(): self.advance(); continue
            if c.isdigit():
                n=''
                while self.peek() and self.peek().isdigit(): n+=self.advance()
                tokens.append(Token('INT',n,self.line)); continue
            if c.isalpha() or c=='_':
                i=''
                while self.peek() and (self.peek().isalnum() or self.peek()=='_'): i+=self.advance()
                t=i.upper() if i in KEYWORDS else 'ID'
                tokens.append(Token(t,i,self.line)); continue
            if c=='=' and self.peek(1)=='=':
                self.advance(); self.advance(); tokens.append(Token('EQ','==',self.line)); continue
            if c=='!' and self.peek(1)=='=':
                self.advance(); self.advance(); tokens.append(Token('NE','!=',self.line)); continue
            if c=='<' and self.peek(1)=='=':
                self.advance(); self.advance(); tokens.append(Token('LE','<=',self.line)); continue
            if c=='>' and self.peek(1)=='=':
                self.advance(); self.advance(); tokens.append(Token('GE','>=',self.line)); continue
            single={'+':'PLUS','-':'MINUS','*':'MUL','/':'DIV',
                    '(':'LPAREN',')':'RPAREN','{':'LBRACE','}':'RBRACE',
                    ';':'SEMICOLON',':':'COLON',',':'COMMA',
                    '=':'ASSIGN','<':'LT','>':'GT'}
            if c in single:
                tokens.append(Token(single[c],c,self.line))
                self.advance(); continue
            raise Exception(f"Caractere inválido '{c}' linha {self.line}")
        tokens.append(Token('EOF','',self.line))
        return tokens

# AST
class Program: 
    def __init__(self,s): self.stmts=s
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
class FuncDecl:
    def __init__(self,n,p,b): self.name=n; self.params=p; self.body=b
class Return:
    def __init__(self,e): self.expr=e
class Call:
    def __init__(self,n,a): self.name=n; self.args=a
class Int:
    def __init__(self,v): self.value=v
class Bool:
    def __init__(self,v): self.value=v
class Var:
    def __init__(self,n): self.name=n
class BinOp:
    def __init__(self,l,o,r): self.left=l; self.op=o; self.right=r
def print_ast(node, indent=0):
    pad = '  ' * indent
    print(f"{pad}{node.__class__.__name__}")

    for value in vars(node).values():
        if isinstance(value, list):
            for item in value:
                if hasattr(item, '__dict__'):
                    print_ast(item, indent + 1)
        elif hasattr(value, '__dict__'):
            print_ast(value, indent + 1)
# PARSER
class Parser:
    def __init__(self,t): self.t=t; self.p=0
    def cur(self): return self.t[self.p]
    def eat(self,x):
        if self.cur().type==x: self.p+=1
        else: raise Exception(f"Esperado {x} linha {self.cur().line}")

    def parse(self):
        s=[]
        while self.cur().type!='EOF': s.append(self.statement())
        return Program(s)

    def statement(self):
        if self.cur().type=='VAR': return self.var_decl()
        if self.cur().type=='DEF': return self.func_decl()
        if self.cur().type=='RETURN': return self.return_stmt()
        if self.cur().type=='PRINT': return self.print_stmt()
        if self.cur().type=='IF': return self.if_stmt()
        if self.cur().type=='WHILE': return self.while_stmt()
        if self.cur().type=='ID': return self.assign()
        raise Exception("Comando inválido")

    def block(self):
        s=[]; self.eat('LBRACE')
        while self.cur().type!='RBRACE': s.append(self.statement())
        self.eat('RBRACE'); return s

    def func_decl(self):
        self.eat('DEF'); name=self.cur().value; self.eat('ID')
        self.eat('LPAREN'); params=[]
        if self.cur().type!='RPAREN':
            params.append(self.cur().value); self.eat('ID')
            while self.cur().type=='COMMA':
                self.eat('COMMA'); params.append(self.cur().value); self.eat('ID')
        self.eat('RPAREN'); self.eat('COLON'); self.eat(self.cur().type)
        body=self.block()
        return FuncDecl(name,params,body)

    def return_stmt(self):
        self.eat('RETURN'); e=self.expr(); self.eat('SEMICOLON')
        return Return(e)

    def var_decl(self):
        self.eat('VAR'); n=self.cur().value; self.eat('ID')
        self.eat('COLON'); self.eat(self.cur().type)
        self.eat('ASSIGN'); e=self.expr(); self.eat('SEMICOLON')
        return VarDecl(n,None,e)

    def assign(self):
        n=self.cur().value; self.eat('ID')
        if self.cur().type=='LPAREN': return self.call_stmt(n)
        self.eat('ASSIGN'); e=self.expr(); self.eat('SEMICOLON')
        return Assign(n,e)

    def call_stmt(self,n):
        self.eat('LPAREN'); a=[]
        if self.cur().type!='RPAREN':
            a.append(self.expr())
            while self.cur().type=='COMMA':
                self.eat('COMMA'); a.append(self.expr())
        self.eat('RPAREN'); self.eat('SEMICOLON')
        return Call(n,a)

    def print_stmt(self):
        self.eat('PRINT'); e=self.expr(); self.eat('SEMICOLON')
        return Print(e)

    def if_stmt(self):
        self.eat('IF'); self.eat('LPAREN')
        c=self.expr(); self.eat('RPAREN')
        t=self.block(); e=None
        if self.cur().type=='ELSE': self.eat('ELSE'); e=self.block()
        return If(c,t,e)

    def while_stmt(self):
        self.eat('WHILE'); self.eat('LPAREN')
        c=self.expr(); self.eat('RPAREN')
        return While(c,self.block())

    def expr(self):
        n=self.simple()
        if self.cur().type in ('LT','GT','EQ','NE','LE','GE'):
            o=self.cur().value; self.eat(self.cur().type)
            n=BinOp(n,o,self.simple())
        return n

    def simple(self):
        n=self.term()
        while self.cur().type in ('PLUS','MINUS'):
            o=self.cur().value; self.eat(self.cur().type)
            n=BinOp(n,o,self.term())
        return n

    def term(self):
        t=self.cur()
        if t.type=='INT': self.eat('INT'); return Int(t.value)
        if t.type in ('TRUE','FALSE'): self.eat(t.type); return Bool(t.value)
        if t.type=='ID':
            self.eat('ID')
            if self.cur().type=='LPAREN':
                self.eat('LPAREN'); a=[]
                if self.cur().type!='RPAREN':
                    a.append(self.expr())
                    while self.cur().type=='COMMA':
                        self.eat('COMMA'); a.append(self.expr())
                self.eat('RPAREN')
                return Call(t.value,a)
            return Var(t.value)
        raise Exception("Expressão inválida")

# SEMÂNTICO (básico)
class Semantic:
    def __init__(self): self.funcs=set()
    def visit(self,n):
        if isinstance(n,Program):
            for s in n.stmts: self.visit(s)
        if isinstance(n,FuncDecl):
            if n.name in self.funcs: raise Exception("Função duplicada")
            self.funcs.add(n.name)
            for s in n.body: self.visit(s)
        if isinstance(n,Call):
            if n.name not in self.funcs: raise Exception("Função não declarada")

# CODEGEN
class Generator:
    def gen_block(self,s,i): return ''.join('    '*i+self.gen(x)+'\n' for x in s)
    def gen(self,n):
        if isinstance(n,Program): return ''.join(self.gen(s)+'\n' for s in n.stmts)
        if isinstance(n,FuncDecl):
            h=f"def {n.name}({','.join(n.params)}):\n"
            return h+self.gen_block(n.body,1)
        if isinstance(n,Return): return f"return {self.gen(n.expr)}"
        if isinstance(n,Call): return f"{n.name}({','.join(self.gen(a) for a in n.args)})"
        if isinstance(n,VarDecl): return f"{n.name} = {self.gen(n.expr)}"
        if isinstance(n,Assign): return f"{n.name} = {self.gen(n.expr)}"
        if isinstance(n,Print): return f"print({self.gen(n.expr)})"
        if isinstance(n,If):
            c=f"if {self.gen(n.cond)}:\n"+self.gen_block(n.then_block,1)
            if n.else_block: c+="else:\n"+self.gen_block(n.else_block,1)
            return c.rstrip()
        if isinstance(n,While):
            return f"while {self.gen(n.cond)}:\n"+self.gen_block(n.block,1).rstrip()
        if isinstance(n,Int): return n.value
        if isinstance(n,Bool): return 'True' if n.value=='true' else 'False'
        if isinstance(n,Var): return n.name
        if isinstance(n,BinOp): return f"({self.gen(n.left)} {n.op} {self.gen(n.right)})"

# MAIN
if __name__=='__main__':
    codigo = open('teste.ml').read()
    tokens = Lexer(codigo).tokenize()
    #IMPRIMIR TOKENS
    if '--tokens' in sys.argv:
        for t in tokens:
            print(t)
        sys.exit(0)
    ast = Parser(tokens).parse()
    #IMPRIMIR AST
    if '--ast' in sys.argv:
        print_ast(ast)
        sys.exit(0)
    #FLUXO NORMAL
    Semantic().visit(ast)
    py = Generator().gen(ast)
    open('saida.py','w').write(py)
    print("Código gerado com sucesso!")