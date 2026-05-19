import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import { RecommendationProvider } from './state/recommendationStore'
import { AuthProvider } from './state/authStore'
import { ProfileProvider } from './state/profileStore'
import AuthGuard from './components/AuthGuard'
import AuthenticatedHeader from './components/AuthenticatedHeader'
import './index.css'

const Preferences = lazy(() => import('./pages/Preferences'))
const Flight = lazy(() => import('./pages/Flight'))
const Detail = lazy(() => import('./pages/Detail'))
const Compare = lazy(() => import('./pages/Compare'))
const Profile = lazy(() => import('./pages/Profile'))
const History = lazy(() => import('./pages/History'))
const Login = lazy(() => import('./pages/Login'))
const Register = lazy(() => import('./pages/Register'))
const Profiles = lazy(() => import('./pages/Profiles'))

type RootedElement = HTMLElement & { __reactRoot?: ReactDOM.Root }

const rootElement = document.getElementById('root') as RootedElement | null
if (!rootElement) throw new Error('Failed to find the root element')

const root = rootElement.__reactRoot ?? ReactDOM.createRoot(rootElement)
rootElement.__reactRoot = root

const guarded = (element: React.ReactNode) => (
  <AuthGuard>
    <Suspense fallback={null}>{element}</Suspense>
  </AuthGuard>
)

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <ProfileProvider>
          <RecommendationProvider>
            <AuthenticatedHeader />
            <Routes>
              <Route
                path="/login"
                element={
                  <Suspense fallback={null}>
                    <Login />
                  </Suspense>
                }
              />
              <Route
                path="/register"
                element={
                  <Suspense fallback={null}>
                    <Register />
                  </Suspense>
                }
              />
              <Route path="/profiles" element={guarded(<Profiles />)} />
              <Route path="/preferences" element={guarded(<Preferences />)} />
              <Route path="/flight" element={guarded(<Flight />)} />
              <Route path="/detail/:wineId" element={guarded(<Detail />)} />
              <Route path="/compare" element={guarded(<Compare />)} />
              <Route path="/profile" element={guarded(<Profile />)} />
              <Route path="/history" element={guarded(<History />)} />
              <Route path="/*" element={guarded(<App />)} />
            </Routes>
          </RecommendationProvider>
        </ProfileProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
)
