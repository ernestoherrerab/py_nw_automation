import React, {useEffect, useState} from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';

const flaskServer = process.env.REACT_APP_FLASK_SERVER 

export default function App() {
  const [data, setData] = useState([])
  

  useEffect(() => {
    fetch(flaskServer + 'site_documentation/home').then(res => res.json()).then(res => {
   const chil = []
   for(let i = 0; i < res.data.length; i++){
    	chil.push({...res.data[i], path:res.data[i].name})
   }
   //console.log(chil)
    const str = {id:'root', name:"sites", children:[...chil]}
    setData(str)
    })
  },[])

  const handleDownloadFile = async (node, file) => {
   const path =  "/documentation" + node.path.split("sites")[1]
   
    var el = document.createElement("a")
    el.setAttribute("href",path)
    el.setAttribute("download", file) 
    document.body.appendChild(el)
    el.click();
    el.remove();
  }

  const renderTree = (nodes) => (
    
    <TreeItem onClick={() => !nodes.children ? handleDownloadFile(nodes, nodes.name) :null} key={nodes.id} nodeId={nodes.id} label={nodes.name}>
      {Array.isArray(nodes.children)
        ? nodes.children.map((node) => {
          const pathName = `/${node.name}`
          node.path = nodes.path ? nodes.path + pathName : nodes.name + pathName
          return renderTree(node)
        })
        : null}
    </TreeItem>
  );

  return (
    <div>
      <a href={flaskServer + 'home'} target="_blank" rel="noreferrer">
      <button>Back To Home</button>
      </a>
      <br/>
      <p></p>
      <br/>
      {data ? (<TreeView
          aria-label="rich object"
          defaultCollapseIcon={<ExpandMoreIcon />}
          defaultExpanded={['root']}
          defaultExpandIcon={<ChevronRightIcon />}
          sx={{ height: "100vh", flexGrow: 1, maxWidth: "100vw", overflowY: 'auto', overflowX:"hidden" }}
        >
         { renderTree(data)}
        </TreeView>) : <h2>Loading...</h2>}
        
    </div>
    
  );
}