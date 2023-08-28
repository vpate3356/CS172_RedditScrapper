import logging, sys
import lucene
import os
import json
from org.apache.lucene.store import MMapDirectory, SimpleFSDirectory, FSDirectory, NIOFSDirectory
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField, FloatPoint, FieldType
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig,IndexOptions, DirectoryReader
from org.apache.lucene.search import IndexSearcher, BoostQuery, Query , Sort, SortField
from org.apache.lucene.search.similarities import BM25Similarity
from flask import Flask, render_template, request


logging.disable(sys.maxsize)


app = Flask(__name__)


def retrieve(storedir, query):
   storedir = '/home/cs172/allFilesLib/'


   searchDir = NIOFSDirectory(Paths.get(storedir))
   searcher = IndexSearcher(DirectoryReader.open(searchDir))
   parser = QueryParser("title", StandardAnalyzer())


   parsed_query = parser.parse(query)
   topDocs = searcher.search(parsed_query, 10).scoreDocs
   topkdocs = []
   if len(topDocs) == 0:
       return "No results found!"


   for score_doc in topDocs:
       doc = searcher.doc(score_doc.doc)
       post_info = f"Document ID: {score_doc.doc}{os.linesep}"
       post_info += f"Score: {score_doc.score}{os.linesep}"
       post_info += f"Title: {doc.get('title')}{os.linesep}"
       post_info += f"URL: {doc.get('url')}{os.linesep}"
       post_info += f"Body: {doc.get('body')}{os.linesep}"
      
       comments = []
       for i in range(5):
           comment_author = doc.get(f"comment_author_{i}")
           if comment_author is None: 
               break
           comment_body = doc.get(f"comment_body_{i}")
           comment_upvotes = doc.get(f"comment_upvotes_{i}")
           comment_permalink = doc.get(f"comment_permalink_{i}")
           comment = f"Comment {i + 1}:{os.linesep}"
           comment += f"  Body: {comment_body}{os.linesep}"
           comment += f"  Author: {comment_author}{os.linesep}"
           comment += f"  Upvotes: {comment_upvotes}{os.linesep}"
           comment += f"  Permalink: {comment_permalink}{os.linesep}"
           comments.append(comment)
      
       post_info += os.linesep.join(comments)
       post_info += f"{os.linesep}----------{os.linesep}"
       topkdocs.append(post_info)


   return os.linesep.join(topkdocs)

#home page
@app.route("/")
def home():
   return '<h1> Welcome to Group 14 Reddit Sports Query Page</h1><br> Click Button For Search<br><br><a href="/input">Search</a>'

#input page
@app.route('/input', methods = ['POST', 'GET'])
def input():
   return render_template('input.html')

#output page - calls retreieve function above 
@app.route('/output', methods=['POST', 'GET'])
def output():
    if request.method == 'POST':
        form_data = request.form
        query = form_data['query']
        print(f"this is the query: {query}")

        lucene.initVM(vmargs=['-Djava.awt.headless=true'])
        lucene.getVMEnv().attachCurrentThread()

        docs = retrieve('allFilesLib', str(query))
        print(docs)

        passages = docs.split(os.linesep + '----------' + os.linesep)
        passages = [passage.replace(os.linesep, '<br>') for passage in passages]
        
        output = f"<h3>Query: {query}</h3><br><br>"
        counter = 1
        for passage in passages:
            output += f"----------------------------------------------NEW POST #{counter}----------------------------------------------<br><br>"
            output += passage
            output += "<br>"
            counter += 1
            if counter > 10:
                break

        output += '<br><a href="/input">Back to Input</a>'
        return output

    else:
        return "Nothing"


  
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
