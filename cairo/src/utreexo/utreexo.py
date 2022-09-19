#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json

from starkware.cairo.lang.vm.crypto import pedersen_hash

class Node:
    def __init__(self, key, left=None, right=None):
        self.parent = None
        self.left = left
        self.right = right
        self.val = key


# [T_1, T_2, T_4, T_8, ... ]
forest = [ None ] * 27

leaves = dict()


def parent_node(root1, root2):
    root = pedersen_hash(root1.val, root2.val)
    root_node = Node(root, root1, root2)
    root1.parent = root_node
    root2.parent = root_node
    return root_node 


def utreexo_add(vout_hash):
    print('add', vout_hash)
    leaf = int(vout_hash, 16)

    if leaf in leaves:
        raise Exception('Leaf exists already')
    n = Node(leaf)
    leaves[leaf] = n
    h = 0 
    r = forest[h]
    while r != None:
        n = parent_node(r, n)
        forest[h] = None
        
        h = h + 1
        r = forest[h]

    forest[h] = n
    return forest


def get_proof(leaf_node):
    if leaf_node.parent == None:
        return [], 0
    
    parent = leaf_node.parent
    proof, tree_index = get_proof(parent)

    if leaf_node == parent.left:
        proof.append(parent.right)
        tree_index = tree_index * 2 
    else:
        proof.append(parent.left)
        tree_index = tree_index * 2 + 1

    return proof, tree_index


def utreexo_delete(vout_hash):
    print('delete', vout_hash)
    leaf = int(vout_hash, 16)

    leaf_node = leaves[leaf]
    del leaves[leaf]

    proof, tree_index = get_proof(leaf_node)

    n = None
    h = 0
    while h < len(proof):
        p = proof[h] # Iterate over each proof element
        if n != None:
            n = parent_node(p, n)
        elif forest[h] == None:
            p.parent = None
            forest[h] = p
        else:
            n = parent_node(p, forest[h])
            forest[h] = None
        h = h + 1

    forest[h] = n

    proof = list(map(lambda node: hex(node.val), proof))
    return proof, tree_index



def compute_leaf_index():
    print('Implement me')



class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

        if self.path.startswith('/favicon'):
            return

        if self.path.startswith('/add'):
            vout_hash = self.path.replace('/add/','')
            utreexo_add(vout_hash)
            self.wfile.write(b'element added')
            return

        if self.path.startswith('/delete'):
            vout_hash = self.path.replace('/delete/','')
            proof, tree_index = utreexo_delete(vout_hash)
            self.wfile.write(json.dumps({'leaf_index': tree_index, 'proof': proof }).encode())
            return 



if __name__ == '__main__':
    server = HTTPServer(('localhost', 2121), RequestHandler)
    print('Starting server at http://localhost:2121')
    server.serve_forever()