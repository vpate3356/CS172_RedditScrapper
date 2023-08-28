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

def create_index(jsonfile, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

    store = NIOFSDirectory(Paths.get(dir))

    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    with open(jsonfile, 'r') as file:
        data = json.load(file)

    non_analyzed = FieldType()
    non_analyzed.setStored(True)
    non_analyzed.setTokenized(False)

    for obj in data:
        doc = Document()
        doc.add(TextField("title", obj.get("TITLE", ""), Field.Store.YES))
        doc.add(Field("id", obj.get("ID", ""), non_analyzed))
        doc.add(Field("url", obj.get("URL", ""), non_analyzed))
        doc.add(TextField("body", obj.get("BODY", ""), Field.Store.YES))
        doc.add(Field("author", obj.get("AUTHOR", ""), non_analyzed))
        doc.add(Field("upvotes", str(obj.get("UPVOTES", "")), non_analyzed))
        doc.add(Field("permalink", obj.get("permalink", ""), non_analyzed))
        doc.add(TextField("subreddit", obj.get("subreddit", ""), Field.Store.YES))

        comments = obj.get("comments", [])
        for i, comment in enumerate(comments):
            comment_author = comment.get("author", "")
            comment_body = comment.get("comment body", "")
            comment_upvotes = str(comment.get("upvotes", ""))
            comment_permalink = comment.get("permalink", "")

            doc.add(Field(f"comment_author_{i}", comment_author, non_analyzed))
            doc.add(TextField(f"comment_body_{i}", comment_body, Field.Store.YES))
            doc.add(Field(f"comment_upvotes_{i}", comment_upvotes, non_analyzed))
            doc.add(Field(f"comment_permalink_{i}", comment_permalink, non_analyzed))

        writer.addDocument(doc)

    writer.close()

def retrieve(storedir, query):
    searchDir = NIOFSDirectory(Paths.get(storedir))
    searcher = IndexSearcher(DirectoryReader.open(searchDir))
    parser = QueryParser("title", StandardAnalyzer())

    try:
        parsed_query = parser.parse(query)
        topDocs = searcher.search(parsed_query, 10, Sort(SortField("comment_upvotes", SortField.Type.INT, True))).scoreDocs
        topkdocs = []
        for score_doc in topDocs:
            doc = searcher.doc(score_doc.doc)
            post_info = f"Document ID: {score_doc.doc}{os.linesep}"
            post_info += f"Score: {score_doc.score}{os.linesep}"
            post_info += f"Title: {doc.get('title')}{os.linesep}"
            post_info += f"URL: {doc.get('url')}{os.linesep}"
            post_info += f"Body: {doc.get('body')}{os.linesep}"
            
            comments = []
            for i in range(15):
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

        print(os.linesep.join(topkdocs))

    except Exception as e:
        print(f"An error occurred during search: {e}")


logging.disable(sys.maxsize)
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

create_index('./validJson/isSoccer1.json', 'testvp/')
retrieve('testvp/', 'Zlatan')
