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
const Profile = lazy(() => import('./pages/Profile'))
const History = lazy(() => import('./pages/History'))

type RootedElement = HTMLElement & { __reactRoot?: ReactDOM.Root }

const rootElement = document.getElementById('root') as RootedElement | null
if (!rootElement) throw new Error('Failed to find the root element')

// Reuse the root across HMR module reloads — two roots on the same element
// corrupt React's fiber tree and produce cascading DOM and hook-state errors.
const root = rootElement.__reactRoot ?? ReactDOM.createRoot(rootElement)
rootElement.__reactRoot = root

root.render(
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
          <Route
            path="/profile"
            element={
              <Suspense fallback={null}>
                <Profile />
              </Suspense>
            }
          />
          <Route
            path="/history"
            element={
              <Suspense fallback={null}>
                <History />
              </Suspense>
            }
          />
          <Route path="/*" element={<App />} />
        </Routes>
      </RecommendationProvider>
    </BrowserRouter>
  </React.StrictMode>
)
