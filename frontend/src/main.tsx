import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import type { ThemeConfig } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

const theme: ThemeConfig = {
  token: {
    colorPrimary: '#3b82f6',
    colorBgBase: '#f5f7fb',
    colorTextBase: '#2c3442',
    colorBorder: '#dbe2ee',
    borderRadius: 12,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif",
  },
  components: {
    Layout: {
      bodyBg: '#f5f7fb',
      headerBg: '#ffffff',
      siderBg: '#ffffff',
      triggerBg: '#ffffff',
    },
    Card: {
      colorBgContainer: '#ffffff',
    },
    Input: {
      colorBgContainer: '#ffffff',
    },
    Button: {
      colorBgContainer: '#ffffff',
    },
  },
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={theme}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
