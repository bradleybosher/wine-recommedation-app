import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import './index.css'

const DesignPreview = lazy(() => import('./pages/DesignPreview'))
const Preferences = lazy(() => import('./pages/Preferences'))

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Failed to find the root element')

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route
          path="/design-preview"
          element={
            <Suspense fallback={null}>
              <DesignPreview />
            </Suspense>
          }
        />
        <Route
          path="/preferences"
          element={
            <Suspense fallback={null}>
              <Preferences />
            </Suspense>
          }
        />
        {/* /flight, /detail, /compare land in Phase 3 */}
        <Route path="/*" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
