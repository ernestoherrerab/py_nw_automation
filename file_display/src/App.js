import React, {useEffect, useState} from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';
import axios from "axios"

const dataOld = {
  id: 'root',
  name: 'Parent',
  children: [
    {
      id: '1',
      name: 'Child - 1',
    },
    {
      id: '3',
      name: 'Child - 3',
      children: [
        {
          id: '4',
          name: 'Child - 4',
        },
        {
          id: '5',
          name: 'Child - 4',
          children:[
            {
                id: '41',
                name: 'Child - 4',
              },
            {
                id: '42',
                name: 'Child - 4',
              },
            {
                id: '43',
                name: 'Child - 4',
              },
          ]
        },
        {
          id: '46',
          name: 'Child - 4',
        },
      ],
    },
  ],
};

export default function App() {
  const [data, setData] = useState([])

  useEffect(() => {
    fetch("http://127.0.0.1:8080/site_documentation/home").then(res => res.json()).then(res => {
   const first = {...res.data[0], path:`${res.data[0].name}/`}
   const second = {...res.data[1], path:`${res.data[1].name}/`}
    const str = {id:'root', name:"sites", children:[first,second]}
    setData(str)
    })
  },[])

  const handleDownloadFile = async (node) => {
    const path = node.path.split("sites/")[1]
    console.log(path)
    fetch("http://127.0.0.1:8080/site_documentation/file_download",  { 
	    method: 'POST',
	    body: JSON.stringify({path} ),
	    headers: {
        'Content-Type': 'application/json' 
	      }
      })
  }

  const renderTree = (nodes) => (
    <TreeItem onClick={() => !nodes.children ? handleDownloadFile(nodes) :null} key={nodes.id} nodeId={nodes.id} label={nodes.name}>
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
      
        <TreeView
          aria-label="rich object"
          defaultCollapseIcon={<ExpandMoreIcon />}
          defaultExpanded={['root']}
          defaultExpandIcon={<ChevronRightIcon />}
          sx={{ height: "100vh", flexGrow: 1, maxWidth: "100vw", overflowY: 'auto', overflowX:"hidden" }}
        >
         { renderTree(data)}
        </TreeView>
    </div>
  );
}
