import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import { RecommendationProvider } from './state/recommendationStore'
import './index.css'

const Preferences = lazy(() => import('./pages/Preferences'))
const Flight = lazy(() => import('./pages/Flight'))
const Detail = lazy(() => import('./pages/Detail'))
const Compare = lazy(() => import('./pages/Compare'))

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Failed to find the root element')

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <RecommendationProvider>
        <Routes>
          <Route
            path="/preferences"
            element={
              <Suspense fallback={null}>
                <Preferences />
              </Suspense>
            }
          />
          <Route
            path="/flight"
            element={
              <Suspense fallback={null}>
                <Flight />
              </Suspense>
            }
          />
          <Route
            path="/detail/:wineId"
            element={
              <Suspense fallback={null}>
                <Detail />
              </Suspense>
            }
          />
          <Route
            path="/compare"
            element={
              <Suspense fallback={null}>
                <Compare />
              </Suspense>
            }
          />
          <Route path="/*" element={<App />} />
        </Routes>
      </RecommendationProvider>
    </BrowserRouter>
  </React.StrictMode>
)
