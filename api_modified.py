from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import argparse
import socket
import threading
import queue
from sudoku import Sudoku

q=queue.Queue(1)
q2=queue.Queue(1)
q3=queue.Queue(1)
q4=queue.Queue(1)
q5=queue.Queue(1)
q6=queue.Queue(1)

#class temporária para facilitar testes
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    
    stats={}

    def _set_response(self, response_code=200, content_type='application/json'):
        self.send_response(response_code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_POST(self):
        if self.path == '/solve':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                sudoku = data['sudoku']
                if not q.full():
                    q.put(sudoku)
                solution=q2.get()
                if len(solution)==1:
                    self._set_response()
                    st=json.dumps([list(solution[0][0]),
                                                 list(solution[0][1]),
                                                 list(solution[0][2]),
                                                 list(solution[0][3]),
                                                 list(solution[0][4]),
                                                 list(solution[0][5]),
                                                 list(solution[0][6]),
                                                 list(solution[0][7]),
                                                 list(solution[0][8])])
                    self.wfile.write((st+"\n").encode('utf-8'))
                else:
                    self._set_response(400)
                    self.wfile.write(json.dumps(f'ERROR: {len(solution)} solutions found\n').encode('utf-8'))
            except Exception as e:
                self._set_response(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def do_GET(self):
        if self.path == '/stats':
            q3.put(1)
            all_stats=q4.get()
            rep=json.dumps(all_stats)
            self._set_response()
            self.wfile.write((rep+"\n").encode('utf-8'))
        elif self.path == '/network':
            q5.put(0)
            network_data=q6.get()
            self._set_response()
            self.wfile.write((json.dumps(network_data)+"\n").encode('utf-8'))
        else:
            self._set_response(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))
    #aleterar para mostrar todos os nodes

    def peer_server(port, anchor, handicap):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_addr = s.getsockname()[0]
        s.close()
        nodes=[]
        tasks=[]
        stats={
               "line tasks":0,
               "section tasks":0,
               "sudokus solved":0
               }
        all_stats={}
        line_results={}
        section_results={}
        cur_sudoku=None
        nodes.append('self')
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.settimeout(0.1)
        server_socket.bind(('0.0.0.0',port))
        print(f'Starting P2P server on port {port}')
        stage=0
        status=0
        if anchor is not None:
            a_host, a_port = anchor.split(':')
            a_port = int(a_port)
            msg = json.dumps({"method":"join"})
            server_socket.sendto(msg.encode(), (a_host, a_port))
        while True:
            #check queue for requests
            if not q.empty():
                cur_sudoku=q.get()
            #algorithm management process
            if cur_sudoku is not None:
                if stage==0:
                    for i in range(9):
                        cur_node=nodes[i%len(nodes)]
                        if cur_node!='self':
                            msg=json.dumps({"method":"line_task","args":{"puzzle":cur_sudoku,"row":i}})
                            server_socket.sendto(msg.encode(), cur_node)
                        else:
                            tasks.append(("self", "line", cur_sudoku, i))
                    stage=1
                elif stage==1:
                    if len(line_results)==9:
                        stage=2
                elif stage==2:
                    for i in range(3):
                        cur_node=nodes[i%len(nodes)]
                        if cur_node!='self':
                            msg=json.dumps({"method":"section_task","args":{"puzzle":cur_sudoku,"section":i, "rows":[line_results[i*3],line_results[i*3+1],line_results[i*3+2]]}})
                            server_socket.sendto(msg.encode(), cur_node)
                        else:
                            tasks.append(("self", "section", cur_sudoku, i, [line_results[i*3],line_results[i*3+1],line_results[i*3+2]]))
                    stage=3
                elif stage==3:
                    if len(section_results)==3:
                        stage=4
                elif stage==4:
                    sudoku_to_solve=Sudoku(cur_sudoku)
                    print("Processing solution")
                    cur_solution=sudoku_to_solve.get_it_solved(section_results[0],section_results[1],section_results[2], 0.01*handicap, 10, 5)
                    stats["sudokus solved"] += 1
                    if not q2.full():
                        q2.put(cur_solution)
                    #reset variables
                    cur_sudoku=None
                    line_results={}
                    section_results={}
                    stage=0
            #process stat request
            if not q3.empty():
                status=q3.get()
            if status==1:
                stats_received=0
                all_stats["all"]={}
                all_stats["all"]["line tasks"]=stats["line tasks"]
                all_stats["all"]["section tasks"]=stats["section tasks"]
                all_stats["all"]["sudokus solved"]=stats["sudokus solved"]
                all_stats["nodes"]=[]
                all_stats["nodes"].append({
                    "address":str(ip_addr)+":"+str(port),
                    "line tasks":stats["line tasks"],
                    "section tasks":stats["section tasks"],
                    "sudokus solved": stats["sudokus solved"]
                })
                for i in nodes:
                    if i != "self":
                        msg = json.dumps({"method":"stat_req"})
                        server_socket.sendto(msg.encode(), i)
                status=2
            elif status==2:
                if stats_received==len(nodes)-1:
                    status=3
            elif status==3:
                q4.put(all_stats)
                status=0
            #process network request
            if not q5.empty():
                q5.get()
                network_data={}
                for i in nodes:
                    if i=="self":
                        network_data[str(ip_addr)+":"+str(port)]=[]
                        for j in nodes:
                            if j!="self":
                                network_data[str(ip_addr)+":"+str(port)].append(j[0]+":"+str(j[1]))
                    else:
                        network_data[i[0]+":"+str(i[1])]=[]
                        for j in nodes:
                            if j!=i:
                                if j=="self":
                                    network_data[i[0]+":"+str(i[1])].append(str(ip_addr)+":"+str(port))
                                else:
                                    network_data[i[0]+":"+str(i[1])].append(j[0]+":"+str(j[1]))
                q6.put(network_data)
            #check for new messages
            try:
                payload, addr = server_socket.recvfrom(4096)
                if len(payload)==0:
                    payload=None
            except socket.timeout:
                payload=None
            #process received messages
            if payload is not None:
                output = json.loads(payload.decode())
                if output["method"]=="join":
                    if len(output)==1:
                        nodes.append(addr)
                        print(f'Connected to: {addr}')
                        node_list = nodes
                        node_list.remove("self")
                        node_list.remove(addr)
                        msg = json.dumps({"method":"join_rep","args":{"node_list":node_list}})
                        server_socket.sendto(msg.encode(), addr)
                        msg = json.dumps({"method":"join","args":{"from":addr}})
                        for i in node_list:
                            server_socket.sendto(msg.encode(), i)
                        node_list.append("self")
                        node_list.append(addr)
                    else:
                        nodes.append(tuple(output["args"]["from"]))
                        print(f'Connected to: {tuple(output["args"]["from"])}')
                elif output["method"]=="join_rep":
                    nodes.append(addr)
                    print(f'Connected to: {addr}')
                    for i in output["args"]["node_list"]:
                        nodes.append(tuple(i))
                        print(f'Connected to: {tuple(i)}')
                elif output["method"]=="line_task":
                    tasks.append((addr, "line", output["args"]["puzzle"], output["args"]["row"]))
                elif output["method"]=="line_task_rep":
                    line_results[output["args"]["row"]]=output["args"]["result"]
                elif output["method"]=="section_task":
                    tasks.append((addr, "section", output["args"]["puzzle"], output["args"]["section"], output["args"]["rows"]))
                elif output["method"]=="section_task_rep":
                    section_results[output["args"]["section"]]=output["args"]["result"]
                elif output["method"]=="stat_req":
                    msg=json.dumps({"method":"stat_rep","args":{"stats":stats}})
                    server_socket.sendto(msg.encode(), addr)
                elif output["method"]=="stat_rep":
                    all_stats["nodes"].append({
                        "address":str(addr[0])+":"+str(addr[1]),
                        "line tasks":output["args"]["stats"]["line tasks"],
                        "section tasks":output["args"]["stats"]["section tasks"],
                        "sudokus solved":output["args"]["stats"]["sudokus solved"]
                    })
                    all_stats["all"]["line tasks"]+=output["args"]["stats"]["line tasks"]
                    all_stats["all"]["section tasks"]+=output["args"]["stats"]["section tasks"]
                    all_stats["all"]["sudokus solved"]+=output["args"]["stats"]["sudokus solved"]
                    stats_received+=1
            #check for tasks
            if len(tasks)>0:
                cur_task=tasks.pop()
                if cur_task[1]=="line":
                    print(f'Processing line {cur_task[3]+1}')
                    sudoku_to_solve=Sudoku(cur_task[2])
                    result=sudoku_to_solve.generate_rows(cur_task[3], 0.01*handicap, 10, 5)
                    stats["line tasks"] += 1
                    if(cur_task[0]!="self"):
                        msg=json.dumps({"method":"line_task_rep","args":{"result":result, "row":cur_task[3]}})
                        server_socket.sendto(msg.encode(), cur_task[0])
                    else:
                        line_results[cur_task[3]]=result
                elif cur_task[1]=="section":
                    print(f'Processing section {cur_task[3]+1}')
                    sudoku_to_solve=Sudoku(cur_task[2])
                    result=sudoku_to_solve.get_valid_sections(cur_task[3],cur_task[4][0],cur_task[4][1],cur_task[4][2], 0.01*handicap, 10, 5)
                    stats["section tasks"] += 1
                    if(cur_task[0]!="self"):
                        msg=json.dumps({"method":"section_task_rep","args":{"result":result, "section":cur_task[3]}})
                        server_socket.sendto(msg.encode(), cur_task[0])
                    else:
                        section_results[cur_task[3]]=result

def run(http_port, p2p_port, anchor, handicap):
    handler = SimpleHTTPRequestHandler
    handler.handicap = handicap
    server_address = ('', http_port)
    httpd = HTTPServer(server_address, handler)
    threading.Thread(target=httpd.serve_forever).start()
    threading.Thread(target=handler.peer_server, args=(p2p_port, anchor, handicap)).start()
    print(f'HTTP server started on port {http_port}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Sart a sudoku solver node')
    parser.add_argument('-p','--http-port',type=int,default=8001, help='Port for http server')
    parser.add_argument('-s','--p2p-port',type=int,default=7000, help='Port for p2p protocol')
    parser.add_argument('-a','--anchor',type=str, help='Anchor node address for P2P network')
    parser.add_argument('-H','--handicap',type=int, default=1, help='Handicap in milliseconds for validation') 
    
    args = parser.parse_args()
    run(args.http_port, args.p2p_port, args.anchor, args.handicap)  

    
