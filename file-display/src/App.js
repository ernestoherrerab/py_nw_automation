import React, {useEffect, useState} from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';

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
    fetch("http://127.0.0.1:8080/site_documentation/home",  {
      'Access-Control-Allow-Origin':"*"
  }).then(res => res.json()).then(res => {
    const {data} = res
    const newData = []
     const restructure = (nodes) => {
      (Object.entries(nodes) || []).map(([key, value], i) => {
        const children = []
        for (const key in value) {
          children.push({id:key, name:key, children:value[key]})
        }
          
        	newData.push({id:i, name:key, children})
      })
     }
     restructure(data)
     console.log(newData)
      setData(newData)
    })
  },[])

  const renderTree = (nodes) => (
    <TreeItem key={nodes.id} nodeId={nodes.id} label={nodes.name}>
      {Array.isArray(nodes.files)
        ? nodes.files.map((node) => renderTree(node))
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
          sx={{ height: "100vh", flexGrow: 1, maxWidth: "100vw", overflowY: 'auto' }}
        >
         { renderTree(dataOld)}
        </TreeView>
    </div>
  );
}
