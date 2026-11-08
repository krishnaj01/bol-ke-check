import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { AboutPage } from './pages/AboutPage'
import { CheckPage } from './pages/CheckPage'
import { UploadPage } from './pages/UploadPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<UploadPage />} />
          <Route path="check/:id" element={<CheckPage />} />
          <Route path="about" element={<AboutPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
