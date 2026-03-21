import { Layout, Dropdown, Avatar, Space } from 'antd'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import styles from './Header.module.css'

const { Header: AntHeader } = Layout

interface HeaderProps {
  collapsed?: boolean
}

export default function Header({ collapsed }: HeaderProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const menuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人设置',
      onClick: () => navigate('/profile'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <AntHeader className={`${styles.header} ${collapsed ? styles.headerCollapsed : ''}`}>
      <div className={styles.title}>
        猫课客户关系管理系统
      </div>
      <div className={styles.user}>
        <Dropdown menu={{ items: menuItems }} placement="bottomRight">
          <Space className={styles.userLink}>
            <Avatar
              size="small"
              icon={<UserOutlined />}
              src={user?.avatar_url}
              style={{ backgroundColor: '#0071e3' }}
            />
            <span className={styles.userName}>{user?.real_name || user?.username}</span>
          </Space>
        </Dropdown>
      </div>
    </AntHeader>
  )
}
