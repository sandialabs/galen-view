''' Module to create the user interface for Jupyter to explore the CORD dataset.
'''

import pickle
import param
import pandas as pd
import panel as pn
import numpy as np
import holoviews as hv
from bokeh.models import HoverTool, LinearColorMapper
from whoosh import index
from whoosh.fields import SchemaClass, TEXT, KEYWORD, ID, STORED
from whoosh.qparser import QueryParser
import cotools
from IPython.core.display import display, HTML

hover = HoverTool(tooltips = [
    ("title", "@title")
])

class DocumentSetExplorer(param.Parameterized):
    ''' The main interface

    This class uses the param library to define a user
    interface.
    '''
    search = param.String(default='')
    coloring = param.ObjectSelector(default="Blue", objects=['Blue'])
    
    def __init__(self, data_dir=".", scoring_cols=None):
        ''' Create a new instance of DocumentSetExplorer

        Parameters
        ----------
        
        data_dir : path
            A path to a directory containing the documents, the whoose library, and 
            the metadata pandas DataFrame.
        '''
        df = pd.read_pickle("metadata.df.pickle") 
        self.allpapers=cotools.Paperset(data_dir)
        self.thedata = df
        self.param.coloring.objects = ["Blue"]+(list(scoring_cols) if scoring_cols is not None else [])
        self.reader = index.open_dir(data_dir)
        self.allpoints = hv.Points(self.thedata, ["X", "Y"]).opts(alpha=0.0)
        self.posxy=hv.streams.Tap(source=self.allpoints, x=0, y=0)
        self.doc = hv.DynamicMap(self.tap_points, streams=[self.posxy]).opts(width=800)
        self.minidoc = hv.DynamicMap(self.tap_points_small, streams=[self.posxy])
        
    
    @param.depends('search', 'coloring')
    def load_points(self):
        ''' Redraw the points
        
        This function runs the query, chooses the color scheme, and creates the points.
        "selected" contains the hv.Points that matched a query, "other_points" are those that 
        don't, and self.allpoints is an invisible layer over all of them that captures and
        responds to hovering and clicks.
        '''
        if len(self.search.strip()) > 0:
            qp = QueryParser("content", schema=self.reader.schema)
            q = qp.parse(self.search)
            with self.reader.searcher() as s:
                resultids = set([r["paperid"] for r in s.search(q, limit=500)])
            selected = [i in resultids for i in range(0,len(self.thedata))]
        else:
            selected = [False]*len(self.allpoints)
        selected_points = hv.Points(self.thedata[selected], ["X", "Y"]).opts(width=700, height=700, marker="triangle", size=7, tools=[hover])
        if self.coloring=="Blue":
            other_points = hv.Points(self.thedata[[not x for x in selected]], ["X", "Y"]).opts(size=5, tools=[hover], alpha=0.4)
        else:
            lowhigh = np.percentile(self.thedata[self.coloring], [0.3, 20])
            color_mapper = LinearColorMapper(palette='Cividis256', low=lowhigh[0], high=lowhigh[1])
            other_points = hv.Points(self.thedata[[not x for x in selected]], ["X", "Y"]).opts(
                size=5, 
                tools=[hover], 
                alpha=0.4, 
                color={'field':self.coloring, 'transform': color_mapper})

        return other_points * selected_points * self.allpoints
    
    def tap_points(self, x,y):
        ''' Returns the full document visualization for the document nearest x,y

        Parameters
        ----------

        x : int
           The x point where the user clicked.

        y : int
           The y point where the user clicked.

        returns : an hv.Div object with the full text.
        '''
        selected_num = self.closest_point((x,y))
        content = self.allpapers[selected_num]["metadata"]["title"] + "<hr>"+cotools.text(self.allpapers[selected_num])
        return hv.Div(content).opts(width=900)
    
    def tap_points_small(self, x,y):
        ''' Returns the partial document visualization for the document nearest x,y

        Parameters
        ----------

        x : int
           The x point where the user clicked.

        y : int
           The y point where the user clicked.

        returns : an hv.Div object with the full text.
        '''
        selected_num = self.closest_point((x,y))
        content = self.allpapers[selected_num]["metadata"]["title"] + "<hr>"+cotools.text(self.allpapers[selected_num])[0:1500]
        return hv.Div(content).opts(width=500, height=500)
    

    def closest_point(self, point):
        ''' Find the closes document to the point provided.

        This could be made faster with something like a red/black tree.
        It works fast enough for 60K points, but this should be improved 
        to scale to large document sets.
        '''
        nodes = np.asarray(self.thedata[["X", "Y"]])
        dist_2 = np.sum((nodes - point)**2, axis=1)
        return np.argmin(dist_2)

    def main_viz(self):
        return pn.Tabs(("Visualization", pn.Row(pn.Column(self.param, self.load_points), self.minidoc)), ("Document", self.doc))

def jupyter_viz(data_dir="."):
    ''' Make the visualization work in Jupyter

    This directs Jupyter to use the full width of the browser.  Then it
    creates and runs the main visualization. Code like this would normally 
    be part of a notebook, but it is included here for simplicity.
    '''
    display(HTML("<style>.container { width:100% !important; }</style>"))

    hv.extension('bokeh')
    d = DocumentSetExplorer()
    return d.main_viz()
    
