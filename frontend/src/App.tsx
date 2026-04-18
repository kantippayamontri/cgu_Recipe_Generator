import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { Footer } from './components/Footer.tsx'
import { Navbar } from './components/Navbar.tsx'
import { Home } from './pages/Home.tsx'
import { RecipeDetail } from './pages/RecipeDetail.tsx'
import { SearchResults } from './pages/SearchResults.tsx'

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen flex-col bg-surface">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<SearchResults />} />
            <Route path="/recipes/:id" element={<RecipeDetail />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  )
}

export default App
