''' Data dowloading and preparation for Galen-View

This module provides function for three things: 1) downloading the 
cord-19 data set (via the cord-19-tools library), 2) analyzing the 
natural language text, producing a 2D layout of the documents, and 
3) indexing all the documents using the whoosh library.

These functions can be used individually, but for convenience, 
this module can be run directly to perform all the steps:

python3 -m sandia.galen.dataprep [test]

If "test" is appended on the command line, only the first 500
documents will be analyzed.  This can be useful for testing
because the full analysis can take up to 90 minutes.
'''

import pandas as pd
from os import path
from shutil import copyfile
import sys
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from whoosh import index
from whoosh.fields import SchemaClass, TEXT, KEYWORD, ID, STORED, NUMERIC
import cotools

class Cord19Schema(SchemaClass):
    ''' Schema for whoosh

    Required for whoose to know how to index the documents.
    '''
    paperid = NUMERIC(stored=True)
    title = TEXT(stored=True)
    content = TEXT

def download_data():
    ''' Download the data if needed

    This function uses the cord-19-tools library to
    download the files.  Running this function in an empty 
    directory will result in the latest version of the
    data being downloaded.

    Note that if the data already appears to be downloaded,
    this function will skip this step.

    returns : nothing
    '''
    if not path.exists("metadata.csv"):
        print("Downloading the metadata file")
        r = requests.get("https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/metadata.csv")
        with open("metadata.csv", "wb") as f:
            f.write(r.content)
    else:
        print("Metadata Already Downloaded")
    
    if not path.exists("comm_use_subset"):
        print("Downloading the CORD-19 Dataset")
        try:
            cotools.download()
        except:
            print("cotools had some problems downloading some of the data.  Continuing with downloaded data")
    else:
        print("Dataset already download")

def make_coords(paper_directory=".", num_docs=None, write_df=False):
    ''' Analyze the documents, creating a 2D layout for visualization.

    This funciton also optionally writes the DataFrame needed by the
    visualization.

    Parameters
    ----------

    paper_directory : str
        A path to a directory where the data has been downloaded.

    num_docs : int
        The number of documents to analyze.  This is mostly for testing.
        Set this to a small number to analyze only the first num_docs 
        documents.

    write_df : boolean
        Whether a pandas.DataFrame should be written in paper_directory
        that contains the titles and the coordinates.  If this is False,
        you must write the DataFrame yourself.  

    returns : the coordinates computed as a sparse numpy array.
    '''
    allpapers = cotools.Paperset(paper_directory)
    alltitles = []
    def each_paper_text(somepapers, range_min=0, range_max=None):
        for i in range(range_min, len(somepapers) if range_max is None else range_max):
            alltitles.append(somepapers[i]["metadata"]["title"])
            yield(alltitles[-1]+"\n\n"+cotools.text(somepapers[i]))
        
    tfidf_vectorizer = TfidfVectorizer(min_df=20, stop_words='english')
    tfidf_vecs = tfidf_vectorizer.fit_transform(each_paper_text(allpapers, range_max=num_docs))
    tsne_vectorizer = TSNE()
    tsne_vecs = tsne_vectorizer.fit_transform(tfidf_vecs)
    if write_df:
        df = pd.DataFrame(tsne_vecs, columns=["X", "Y"])
        df["title"] = alltitles
        df.to_pickle(path.join(paper_directory, "metadata.df.pickle"))
    return tsne_vecs

def make_index(paper_directory=".", num_docs=None):
    ''' Create a searchable index from the data set.

    Parameters
    ----------
    
    paper_directory : str
        A path to a directory where the data has been downloaded.

    num_docs : int
        The number of documents to analyze.  This is mostly for testing.
        Set this to a small number to analyze only the first num_docs 
        documents.
    
    returns : nothing
    '''    
    allpapers = cotools.Paperset(paper_directory)
    ix = index.create_in(paper_directory, Cord19Schema)
    writer = ix.writer()
    for i in range(0, num_docs if num_docs is not None else len(allpapers)):
        if (i+1) % 100 == 0:
            print(".", end='', flush=True)
        if (i+1) % 1000 == 0:
            print()
        paper_title = allpapers[i]["metadata"]["title"]
        text_content = cotools.text(allpapers[i])
        if len(text_content.strip())==0:
            text_content = paper_title
        writer.add_document(
            paperid=i, 
            title=paper_title, 
            content=cotools.text(allpapers[i]))
    print("\nDone. Committing Index")
    writer.commit()
    print("Done Indexing")

     
if __name__ == "__main__":
    print("Initializing Data in Current Directory")
    print("Checking for Data in this Directory")
    download_data()
    print("========")
    print("Making the Coordinates to Visualize the Data")
    make_coords(num_docs=2000 if sys.argv[-1].lower()=="test" else None, write_df=True)
    print("========")
    print("Building a searchable index from the documents")
    make_index(num_docs=2000 if sys.argv[-1].lower()=="test" else None)
    print("========")
    copyfile(path.join(path.dirname(__file__), "GalenView.ipynb"), "GalenView.ipynb")
    print("Done.  Run \"jupyter-notebook GalenView.ipynb\" and run all cells to explore the data.")
