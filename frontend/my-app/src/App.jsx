import { useEffect, useState } from 'react'
import axios from 'axios'

function App() {
  const [msg, setMsg] = useState('')

  useEffect(() => {
    axios.get('http://localhost:8000/api/hello')
      .then(res => setMsg(res.data.message))
      .catch(err => console.error(err))
  }, [])

  return <h1>{msg || 'Učitavam...'}</h1>
}

export default App
