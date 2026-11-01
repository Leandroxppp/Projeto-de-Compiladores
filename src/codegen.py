from __future__ import annotations
import json, os, subprocess, platform
from .ast_nodes import *

class CppCodeGenerator:
    def __init__(self):
        self.ind=0; self.lines=[]; self.fork_names=set(); self.class_names=set()
        self.remote_forks=set()   # tarefas 'fork ... on computer(...)' (devolvem valor)
        self.func_names=set()     # funcoes de nivel superior (alvos possiveis de fork remoto)
    def w(self,s=''): self.lines.append('    '*self.ind+s)
    def generate(self,p:Program):
        self.class_names={s.name for s in p.statements if isinstance(s,ClassDecl)}
        self.func_names={x.name for x in p.statements if isinstance(x,FuncDecl)}
        self.remote_forks=set()
        self.lines=[]
        self.w('#include <iostream>'); self.w('#include <string>'); self.w('#include <vector>'); self.w('#include <thread>'); self.w('#include <mutex>'); self.w('#include <cmath>'); self.w('#include <chrono>'); self.w('#include <sstream>'); self.w('#include <algorithm>'); self.w('#include <memory>'); self.w('#include <map>'); self.w('#include <functional>'); self.w('#include <stdexcept>'); self.w('#ifdef _WIN32'); self.w('#include <winsock2.h>'); self.w('#include <ws2tcpip.h>'); self.w('#else'); self.w('#include <sys/types.h>'); self.w('#include <sys/socket.h>'); self.w('#include <arpa/inet.h>'); self.w('#include <netinet/in.h>'); self.w('#include <unistd.h>'); self.w('#include <pthread.h>'); self.w('#include <sched.h>'); self.w('#endif'); self.w('#ifdef interface'); self.w('#undef interface'); self.w('#endif'); self.w()
        self.w('std::mutex __minipar_print_mutex;')
        self.w('template<class... T> void mp_print(T&&... xs){ std::lock_guard<std::mutex> g(__minipar_print_mutex); ((std::cout << xs), ...); std::cout << std::endl; }')
        self.w('double mp_number(const std::string& s){ try{return std::stod(s);}catch(...){return 0.0;} }')
        self.w('std::string mp_input(const std::string& p=""){ if(!p.empty()) std::cout<<p; std::string s; std::getline(std::cin,s); return s; }')
        self.w('std::string input_text(const std::string& p=""){ return mp_input(p); }')
        self.w('template<class T> std::string mp_to_string(const T& v){ std::ostringstream o; o<<v; return o.str(); }')
        self.w('std::vector<double> input_list(const std::string& p=""){ if(!p.empty()) std::cout<<p; std::string line; std::getline(std::cin,line); std::stringstream ss(line); std::vector<double> v; double x; while(ss>>x) v.push_back(x); return v; }')
        self.w('double len(const std::vector<double>& v){ return (double)v.size(); }')
        self.w('std::string format_list(const std::vector<double>& v){ std::ostringstream o; o<<"["; for(size_t i=0;i<v.size();++i){ if(i) o<<", "; o<<v[i]; } o<<"]"; return o.str(); }')
        self.w('double now_seconds(){ using clock=std::chrono::steady_clock; return std::chrono::duration<double>(clock::now().time_since_epoch()).count(); }')
        self.w('double cpu_work(double seed){ volatile double acc = seed + 1.0; for(long long k=0;k<80000;++k){ acc = std::fmod(acc * 1.000000119 + (double)k * 0.000001, 1000.0); } return acc; }')
        self.w('std::string mandelbrot_ascii(){ const int largura=50, altura=20, max_iter=100; const std::string chars=" .:-=+#%@"; std::ostringstream out; out<<"=== FRACTAL DE MANDELBROT (Gerado pelo Nucleo 5) ==="<<std::endl; for(int y=0;y<altura;++y){ double cy=((double)y/altura)*2.4-1.2; for(int x=0;x<largura;++x){ double cx=((double)x/largura)*3.0-2.0; double zx=0.0, zy=0.0; int it=0; while(zx*zx+zy*zy<=4.0 && it<max_iter){ double tmp=zx*zx-zy*zy+cx; zy=2.0*zx*zy+cy; zx=tmp; ++it; } int idx=(int)(((double)it/max_iter)*(chars.size()-1)); if(idx<0) idx=0; if(idx>=(int)chars.size()) idx=(int)chars.size()-1; out<<chars[(size_t)idx]; } out<<std::endl; } out<<"===================================================="; return out.str(); }')
        self.w('std::string sierpinski_ascii(){ const int n=27; std::ostringstream out; out<<"=== TAPETE DE SIERPINSKI (Nucleo 6) ==="<<std::endl; for(int y=0;y<n;++y){ for(int x=0;x<n;++x){ int a=x,b=y; bool vazio=false; while(a>0 || b>0){ if(a%3==1 && b%3==1){ vazio=true; break; } a/=3; b/=3; } out<<(vazio?"  ":"##"); } out<<std::endl; } out<<"-> [Nucleo 6] Tapete de Sierpinski renderizado com sucesso na tela!"; return out.str(); }')
        self.w('struct CChannel { std::string host; int port; };')
        self.w('#ifdef _WIN32')
        self.w('using mp_socket_t = SOCKET;')
        self.w('const mp_socket_t MP_INVALID_SOCKET = INVALID_SOCKET;')
        self.w('struct WSAInit { WSAInit(){WSADATA d; WSAStartup(MAKEWORD(2,2),&d);} ~WSAInit(){WSACleanup();} } __wsa;')
        self.w('#define MP_CLOSE closesocket')
        self.w('#else')
        self.w('using mp_socket_t = int;')
        self.w('const mp_socket_t MP_INVALID_SOCKET = -1;')
        self.w('#define MP_CLOSE close')
        self.w('#endif')
        self.w('#ifdef _WIN32')
        self.w('void mp_pin_thread(std::thread& t,int core){ if(core>0) SetThreadAffinityMask((HANDLE)t.native_handle(), (DWORD_PTR)1ULL << (core-1)); }')
        self.w('#else')
        self.w('void mp_pin_thread(std::thread& t,int core){ if(core>0){ cpu_set_t cpuset; CPU_ZERO(&cpuset); CPU_SET(core-1,&cpuset); pthread_setaffinity_np(t.native_handle(),sizeof(cpu_set_t),&cpuset); } }')
        self.w('#endif')
        self.w('std::map<int, mp_socket_t> __mp_client_pending;')
        self.w('std::map<int, mp_socket_t> __mp_server_pending;')
        self.w('void mp_send(const CChannel& c,const std::string& msg){')
        self.ind+=1
        self.w('auto serverIt=__mp_server_pending.find(c.port);')
        self.w('if(serverIt!=__mp_server_pending.end()){ mp_socket_t s=serverIt->second; send(s,msg.c_str(),(int)msg.size(),0); MP_CLOSE(s); __mp_server_pending.erase(serverIt); return; }')
        self.w('mp_socket_t s=socket(AF_INET,SOCK_STREAM,0); if(s==MP_INVALID_SOCKET) throw std::runtime_error("socket()");')
        self.w('sockaddr_in a{}; a.sin_family=AF_INET; a.sin_port=htons(c.port); if(inet_pton(AF_INET,c.host.c_str(),&a.sin_addr)<=0){MP_CLOSE(s); throw std::runtime_error("IP invalido");}')
        self.w('if(connect(s,(sockaddr*)&a,sizeof(a))<0){MP_CLOSE(s); throw std::runtime_error("connect()");}')
        self.w('send(s,msg.c_str(),(int)msg.size(),0); __mp_client_pending[c.port]=s;')
        self.ind-=1
        self.w('}')
        self.w('std::string mp_receive(const CChannel& c){')
        self.ind+=1
        self.w('auto clientIt=__mp_client_pending.find(c.port);')
        self.w('if(clientIt!=__mp_client_pending.end()){ mp_socket_t s=clientIt->second; char b[4096]; int n=recv(s,b,4095,0); std::string r=n>0?std::string(b,b+n):std::string(); MP_CLOSE(s); __mp_client_pending.erase(clientIt); return r; }')
        self.w('mp_socket_t srv=socket(AF_INET,SOCK_STREAM,0); if(srv==MP_INVALID_SOCKET) throw std::runtime_error("socket()"); int yes=1; setsockopt(srv,SOL_SOCKET,SO_REUSEADDR,(const char*)&yes,sizeof(yes));')
        self.w('sockaddr_in a{}; a.sin_family=AF_INET; a.sin_port=htons(c.port); a.sin_addr.s_addr=INADDR_ANY; if(bind(srv,(sockaddr*)&a,sizeof(a))<0){MP_CLOSE(srv); throw std::runtime_error("bind()");}')
        self.w('listen(srv,1); mp_socket_t cli=accept(srv,nullptr,nullptr); MP_CLOSE(srv); if(cli==MP_INVALID_SOCKET) throw std::runtime_error("accept()");')
        self.w('char b[4096]; int n=recv(cli,b,4095,0); std::string r=n>0?std::string(b,b+n):std::string(); __mp_server_pending[c.port]=cli; return r;')
        self.ind-=1
        self.w('}')
        self.w("std::string field(const std::string& text, double index){ std::stringstream ss(text); std::string item; long long alvo=(long long)index; for(long long i=0;i<=alvo;++i){ if(!std::getline(ss,item,'|')) return std::string(); } return item; }")
        self.w('double to_number(const std::string& text){ return mp_number(text); }')
        self.w()
        self.emit_remote_runtime()
        # classes/functions first
        for s in p.statements:
            if isinstance(s,ClassDecl): self.class_decl(s)
        for s in p.statements:
            if isinstance(s,FuncDecl): self.func_decl(s)
        self.emit_worker(p)
        self.w('int main(int argc, char** argv){'); self.ind+=1
        # modo trabalhador: ./programa --worker [porta]  (porta padrao 6000)
        self.w('if (argc >= 2 && std::string(argv[1]) == "--worker") return mp_worker(argc >= 3 ? std::atoi(argv[2]) : 6000);')
        for s in p.statements:
            if not isinstance(s,(ClassDecl,FuncDecl)): self.stmt(s)
        self.w('return 0;'); self.ind-=1; self.w('}')
        return '\n'.join(self.lines)+'\n'
    def ctype(self,typ,val=None):
        if typ in ('int',): return 'long long'
        if typ in ('number','float'): return 'double'
        if typ=='string': return 'std::string'
        if typ=='bool': return 'bool'
        if typ=='list': return 'std::vector<double>'
        if typ in self.class_names:return typ
        if isinstance(val,String):return 'std::string'
        if isinstance(val,Bool):return 'bool'
        if isinstance(val,ListLiteral):return 'std::vector<double>'
        if isinstance(val,Channel):return 'CChannel'
        if isinstance(val,Receive):return 'std::string'
        if isinstance(val,New):return val.class_name
        return 'double'
    def class_decl(self,n):
        base=f' : public {n.superclass}' if n.superclass else ''
        self.w(f'class {n.name}{base} {{'); self.ind+=1; self.w('public:'); self.ind+=1
        attrs=[x for x in n.members if isinstance(x,VarDecl)]
        for a in attrs:self.w(f'{self.ctype(a.declared_type,a.value)} {a.name}{(" = "+self.expr(a.value)) if a.value else "{}"};')
        # permissive constructor for no/args is omitted; default only
        self.w(f'{n.name}() = default;')
        for m in n.members:
            if isinstance(m,FuncDecl): self.method_decl(m)
        self.ind-=2; self.w('};'); self.w()
    def method_decl(self,n):
        params=', '.join('double '+p for p in n.params)
        self.w(f'double {n.name}({params}) {{'); self.ind+=1
        for s in n.body.statements:self.stmt(s)
        self.w('return 0;'); self.ind-=1; self.w('}')
    def func_decl(self,n):
        params=', '.join('double '+p for p in n.params)
        self.w(f'double {n.name}({params}) {{'); self.ind+=1
        for s in n.body.statements:self.stmt(s)
        self.w('return 0;'); self.ind-=1; self.w('}'); self.w()
    def block_body(self,b):
        for s in b.statements:self.stmt(s)
    def stmt(self,n):
        if n is None:return
        if isinstance(n,Block):
            if n.kind=='par':
                names=[]
                for idx,s in enumerate(n.statements):
                    nm=f'__par_{len(self.lines)}_{idx}'; names.append(nm); self.w(f'std::thread {nm}([=]() mutable {{'); self.ind+=1; self.stmt(s); self.ind-=1; self.w('});')
                for nm in names:self.w(f'{nm}.join();')
            else:
                self.w('{'); self.ind+=1; self.block_body(n); self.ind-=1; self.w('}')
        elif isinstance(n,VarDecl): self.w(f'{self.ctype(n.declared_type,n.value)} {n.name}' + (f' = {self.expr(n.value)}' if n.value else '{}') + ';')
        elif isinstance(n,Assignment): self.w(f'{self.expr(n.target)} = {self.expr(n.value)};')
        elif isinstance(n,Print): self.w('mp_print('+', '.join(self.expr(x) for x in n.args)+');')
        elif isinstance(n,If):
            self.w(f'if ({self.expr(n.cond)}) {{'); self.ind+=1; self.stmt_body(n.then_branch); self.ind-=1; self.w('}')
            if n.else_branch:self.w('else {'); self.ind+=1; self.stmt_body(n.else_branch); self.ind-=1; self.w('}')
        elif isinstance(n,While): self.w(f'while ({self.expr(n.cond)}) {{'); self.ind+=1; self.stmt_body(n.body); self.ind-=1; self.w('}')
        elif isinstance(n,For):
            init=self.inline(n.init); cond=self.expr(n.cond) if n.cond else 'true'; inc=self.inline(n.inc)
            self.w(f'for ({init}; {cond}; {inc}) {{'); self.ind+=1; self.stmt_body(n.body); self.ind-=1; self.w('}')
        elif isinstance(n,Return): self.w('return '+(self.expr(n.value) if n.value else '0')+';')
        elif isinstance(n,Break):self.w('break;')
        elif isinstance(n,Continue):self.w('continue;')
        elif isinstance(n,Send):
            parts=' + std::string("|") + '.join(f'mp_to_string({self.expr(x)})' for x in n.payload) if n.payload else 'std::string()'
            self.w(f'mp_send({self.expr(n.channel)}, {parts});')
        elif isinstance(n,Fork):
            if n.target_kind=='computer': self.fork_remote(n)
            else:
                self.fork_names.add(n.task_name); self.w(f'std::thread __fork_{n.task_name}([=]() mutable {{'); self.ind+=1; self.w(f'// alvo solicitado: {n.target_kind}({self.expr(n.target)})'); self.block_body(n.body); self.ind-=1; self.w('});')
                self.w(f'mp_pin_thread(__fork_{n.task_name}, (int)({self.expr(n.target)}));')
        elif isinstance(n,Join):
            for t in n.tasks:
                self.w(f'if (__fork_{t}.joinable()) __fork_{t}.join();')
                if t in self.remote_forks:
                    # se a chamada remota falhou, avisa com clareza e encerra
                    self.w(f'if (!__fork_error_{t}.empty()) {{ std::cerr << "Erro no fork remoto \'{t}\': " << __fork_error_{t} << std::endl; std::exit(1); }}')
        elif isinstance(n,(Call,Property,Identifier,Number,String,Bool,Binary,Unary,New,Receive,Input,ListLiteral,Index)): self.w(self.expr(n)+';')
    def fork_remote(self,n):
        """Gera o C++ de 'fork t on computer("IP:porta") { f(a, b); }'.

        O pai avalia os argumentos AGORA e dispara uma thread que faz a chamada
        pela rede. O valor devolvido fica em __fork_result_t, lido por resultado(t)
        depois do join. Falhas ficam em __fork_error_t e sao tratadas no join.
        """
        stmts=n.body.statements
        if not (len(stmts)==1 and isinstance(stmts[0],Call) and isinstance(stmts[0].callee,Identifier)):
            # corpo invalido: o semantico ja reportou o erro; aqui so evitamos quebrar a geracao
            self.w(f'// fork remoto "{n.task_name}" invalido (veja os erros semanticos)')
            return
        nome=n.task_name; call=stmts[0]
        self.fork_names.add(nome); self.remote_forks.add(nome)
        args=', '.join(f'(double)({self.expr(a)})' for a in call.args)
        self.w(f'double __fork_result_{nome} = 0; std::string __fork_error_{nome};')
        self.w(f'std::vector<double> __fork_args_{nome} = {{{args}}};')
        self.w(f'std::string __fork_dest_{nome} = {self.expr(n.target)};')
        self.w(f'std::thread __fork_{nome}([&__fork_result_{nome}, &__fork_error_{nome}, __fork_args_{nome}, __fork_dest_{nome}]() {{')
        self.ind+=1
        self.w(f'try {{ __fork_result_{nome} = mp_remote_call(__fork_dest_{nome}, "{call.callee.name}", __fork_args_{nome}); }}')
        self.w(f'catch (const std::exception& e) {{ __fork_error_{nome} = e.what(); }}')
        self.ind-=1; self.w('});')

    def emit_remote_runtime(self):
        """Runtime de rede do fork remoto (lado cliente + utilitarios).

        Protocolo de texto, uma linha por mensagem:
          pedido:   RUN <funcao> <n_args> <arg1> ... <argN>
          resposta: OK <valor>   |   ERR <mensagem>
        """
        for line in REMOTE_RUNTIME.strip('\n').split('\n'): self.w(line)
        self.w()

    def emit_worker(self,p):
        """Tabela de funcoes expostas + modo trabalhador (--worker).

        Cada funcao de nivel superior do programa pode ser chamada por um fork
        remoto. O trabalhador atende cada conexao em uma thread propria, entao
        varios forks para o mesmo computador rodam em paralelo.
        """
        self.w('std::map<std::string, std::pair<int, std::function<double(const std::vector<double>&)>>> mp_funcoes_remotas = {')
        self.ind+=1
        for f in (x for x in p.statements if isinstance(x,FuncDecl)):
            chamada=', '.join(f'a[{i}]' for i in range(len(f.params)))
            param='a' if f.params else ''
            self.w(f'{{"{f.name}", {{{len(f.params)}, [](const std::vector<double>& {param}) -> double {{ return {f.name}({chamada}); }}}}}},')
        self.ind-=1; self.w('};')
        for line in WORKER_RUNTIME.strip('\n').split('\n'): self.w(line)
        self.w()

    def stmt_body(self,n):
        if isinstance(n,Block):self.block_body(n)
        else:self.stmt(n)
    def inline(self,n):
        if n is None:return ''
        if isinstance(n,VarDecl):return f'{self.ctype(n.declared_type,n.value)} {n.name} = {self.expr(n.value) if n.value else "0"}'
        if isinstance(n,Assignment):return f'{self.expr(n.target)} = {self.expr(n.value)}'
        return self.expr(n)
    def expr(self,n):
        if n is None:return '0'
        if isinstance(n,Identifier):return n.name
        if isinstance(n,Number):return n.value
        if isinstance(n,String):return json.dumps(n.value)
        if isinstance(n,Bool):return 'true' if n.value else 'false'
        if isinstance(n,Binary):return f'({self.expr(n.left)} {n.op} {self.expr(n.right)})'
        if isinstance(n,Unary):return f'({n.op}{self.expr(n.expr)})'
        if isinstance(n,Property):return f'{self.expr(n.obj)}.{n.name}'
        if isinstance(n,Call) and isinstance(n.callee,Identifier) and n.callee.name=='resultado' and 'resultado' not in self.func_names and len(n.args)==1 and isinstance(n.args[0],Identifier):
            return f'__fork_result_{n.args[0].name}'   # valor devolvido pelo fork remoto
        if isinstance(n,Call):return f'{self.expr(n.callee)}({", ".join(self.expr(x) for x in n.args)})'
        if isinstance(n,New):return f'{n.class_name}()'
        if isinstance(n,This):return '(*this)'
        if isinstance(n,ListLiteral):return 'std::vector<double>{'+', '.join(self.expr(x) for x in n.items)+'}'
        if isinstance(n,Index):return f'{self.expr(n.obj)}[(size_t)({self.expr(n.index)})]'
        if isinstance(n,Input):return f'mp_number(mp_input({self.expr(n.prompt) if n.prompt else ""}))'
        if isinstance(n,Receive):return f'mp_receive({self.expr(n.channel)})'
        if isinstance(n,Channel):return f'CChannel{{{self.expr(n.host)}, (int)({self.expr(n.port)})}}'
        return '0'

def compile_cpp(code:str,out_base:str):
    cpp=out_base+'.cpp'; exe=out_base+('.exe' if platform.system()=='Windows' else '')
    os.makedirs(os.path.dirname(cpp),exist_ok=True)
    open(cpp,'w',encoding='utf-8').write(code)
    cmd=['g++','-std=c++20','-O3','-pthread',cpp,'-o',exe]
    if platform.system()=='Windows': cmd.append('-lws2_32')
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    return {'ok':p.returncode==0,'cpp':cpp,'exe':exe,'stdout':p.stdout,'stderr':p.stderr,'command':' '.join(cmd)}


# C++ fixo do fork remoto. Mantido como texto para ficar legivel e comentado.
REMOTE_RUNTIME = r'''
#include <cstdlib>
// ---- Fork remoto: utilitarios de socket ----
static bool mp_send_all(mp_socket_t s, const std::string& data){
    size_t off = 0;
    while (off < data.size()) {
        int n = (int)send(s, data.c_str() + off, (int)(data.size() - off), 0);
        if (n <= 0) return false;
        off += (size_t)n;
    }
    return true;
}
// Le ate o fim da linha. Devolve false se a conexao fechou sem nenhum dado.
static bool mp_recv_line(mp_socket_t s, std::string& line){
    line.clear(); char c;
    while (true) {
        int n = (int)recv(s, &c, 1, 0);
        if (n <= 0) return !line.empty();
        if (c == '\n') return true;
        if (c != '\r') line += c;
    }
}
// ---- Fork remoto: lado cliente (programa principal) ----
// destino: "IP" ou "IP:porta" (porta padrao 6000). Lanca excecao em caso de falha.
double mp_remote_call(const std::string& destino, const std::string& funcao, const std::vector<double>& args){
    std::string host = destino; int porta = 6000;
    size_t p = destino.rfind(':');
    if (p != std::string::npos) { host = destino.substr(0, p); porta = std::atoi(destino.substr(p + 1).c_str()); }
    mp_socket_t s = socket(AF_INET, SOCK_STREAM, 0);
    if (s == MP_INVALID_SOCKET) throw std::runtime_error("nao foi possivel criar o socket");
    sockaddr_in a{}; a.sin_family = AF_INET; a.sin_port = htons((unsigned short)porta);
    if (inet_pton(AF_INET, host.c_str(), &a.sin_addr) <= 0) { MP_CLOSE(s); throw std::runtime_error("IP invalido: " + host); }
    if (connect(s, (sockaddr*)&a, sizeof(a)) < 0) {
        MP_CLOSE(s);
        throw std::runtime_error("nao foi possivel conectar em " + host + ":" + std::to_string(porta) + " (o worker esta rodando? o firewall liberou a porta?)");
    }
    std::ostringstream req; req.precision(17);
    req << "RUN " << funcao << " " << args.size();
    for (double v : args) req << " " << v;
    req << "\n";
    std::string resp;
    if (!mp_send_all(s, req.str()) || !mp_recv_line(s, resp)) { MP_CLOSE(s); throw std::runtime_error("conexao perdida durante a chamada remota"); }
    MP_CLOSE(s);
    if (resp.rfind("OK ", 0) == 0) return std::strtod(resp.c_str() + 3, nullptr);
    if (resp.rfind("ERR ", 0) == 0) throw std::runtime_error("erro no worker: " + resp.substr(4));
    throw std::runtime_error("resposta invalida do worker: " + resp);
}
'''

WORKER_RUNTIME = r'''
// ---- Fork remoto: lado trabalhador (executavel iniciado com --worker) ----
void mp_worker_conexao(mp_socket_t cli){
    std::string line;
    if (mp_recv_line(cli, line)) {
        std::istringstream in(line); std::string cmd, nome; int n = 0;
        in >> cmd >> nome >> n;
        std::vector<double> args; double v;
        while (in >> v) args.push_back(v);
        std::string resp;
        auto it = mp_funcoes_remotas.find(nome);
        if (cmd != "RUN") resp = "ERR comando desconhecido";
        else if (it == mp_funcoes_remotas.end()) resp = "ERR funcao '" + nome + "' nao existe neste programa";
        else if (n != it->second.first || (int)args.size() != it->second.first) resp = "ERR numero de argumentos invalido para '" + nome + "'";
        else {
            try {
                std::ostringstream chamada; chamada << nome << "(";
                for (size_t k = 0; k < args.size(); ++k) chamada << (k ? ", " : "") << args[k];
                chamada << ")";
                mp_print("[worker] executando ", chamada.str());
                std::ostringstream o; o.precision(17); o << "OK " << it->second.second(args); resp = o.str();
                mp_print("[worker] concluido ", chamada.str());
            }
            catch (const std::exception& e) { resp = std::string("ERR ") + e.what(); }
        }
        mp_send_all(cli, resp + "\n");
    }
    MP_CLOSE(cli);
}
int mp_worker(int porta){
    mp_socket_t srv = socket(AF_INET, SOCK_STREAM, 0);
    if (srv == MP_INVALID_SOCKET) { std::cerr << "worker: socket() falhou" << std::endl; return 1; }
    int yes = 1; setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, (const char*)&yes, sizeof(yes));
    sockaddr_in a{}; a.sin_family = AF_INET; a.sin_port = htons((unsigned short)porta); a.sin_addr.s_addr = INADDR_ANY;
    if (bind(srv, (sockaddr*)&a, sizeof(a)) < 0) { std::cerr << "worker: nao foi possivel usar a porta " << porta << " (ja esta em uso?)" << std::endl; return 1; }
    listen(srv, 16);
    mp_print("[worker] aguardando tarefas na porta ", porta, " (Ctrl+C para encerrar)");
    while (true) {
        mp_socket_t cli = accept(srv, nullptr, nullptr);
        if (cli == MP_INVALID_SOCKET) continue;
        std::thread(mp_worker_conexao, cli).detach();   // uma thread por pedido: forks simultaneos rodam em paralelo
    }
    return 0;
}
'''
