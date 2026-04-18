import { useState } from 'react'
import { Layout, Menu } from 'antd'
import {
  UserOutlined,
  TeamOutlined,
  FileTextOutlined,
  BellOutlined,
  SettingOutlined,
  UploadOutlined,
  AuditOutlined,
  HistoryOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import Header from './Header'
import styles from './AppLayout.module.css'

const { Sider, Content } = Layout

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: '数据概览',
  },
  {
    key: '/customers',
    icon: <TeamOutlined />,
    label: '客户管理',
  },
  {
    key: '/followups',
    icon: <FileTextOutlined />,
    label: '跟进记录',
  },
  {
    key: '/services',
    icon: <AuditOutlined />,
    label: '咨询服务',
  },
  {
    key: '/reminders',
    icon: <BellOutlined />,
    label: '服务提醒',
  },
  {
    key: '/opportunities',
    icon: <DashboardOutlined />,
    label: '销售机会',
  },
  {
    key: '/imports',
    icon: <UploadOutlined />,
    label: '数据导入',
    adminOnly: true,
  },
  {
    key: '/users',
    icon: <UserOutlined />,
    label: '用户管理',
    adminOnly: true,
  },
  {
    key: '/audit',
    icon: <HistoryOutlined />,
    label: '审计日志',
    adminOnly: true,
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: '系统设置',
    adminOnly: true,
  },
] as const

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)

  const isAdmin = user?.role_name === 'admin' || user?.role_name === 'super_admin'

  const filteredMenuItems = menuItems
    .filter((item) => !item.adminOnly || isAdmin)
    .map(({ adminOnly: _, ...item }) => item)

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  return (
    <Layout className={styles.layout}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        className={styles.sider}
        width={240}
        collapsedWidth={80}
      >
        <div className={`${styles.logo} ${collapsed ? styles.logoCollapsed : ''}`}>
          <div className={styles.logoIcon}>
            <span>猫</span>
          </div>
          {!collapsed && <span className={styles.logoText}>猫课 CRM</span>}
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={filteredMenuItems}
          onClick={handleMenuClick}
          className={styles.menu}
        />
      </Sider>
      <Layout className={`${styles.mainLayout} ${collapsed ? styles.mainLayoutCollapsed : ''}`}>
        <Header collapsed={collapsed} />
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
