import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import styles from './LoginPage.module.css'

interface LoginForm {
  username: string
  password: string
}

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [form] = Form.useForm()

  const handleSubmit = async (values: LoginForm) => {
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '登录失败')
        return
      }

      const data = await response.json()

      setAuth(
        {
          id: data.user.id,
          username: data.user.phone || data.user.email || '',
          email: data.user.email,
          phone: data.user.phone,
          real_name: data.user.name,
          avatar_url: null,
          role_id: data.user.role_id,
          role_name: data.user.role_name,
          is_active: data.user.status === 'active',
        },
        data.access_token,
        data.refresh_token
      )

      message.success('登录成功')
      navigate('/')
    } catch (error) {
      message.error('登录失败，请检查网络连接')
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.logoWrapper}>
          <div className={styles.logo}>
            <span>猫</span>
          </div>
        </div>
        <h1 className={styles.title}>猫课 CRM</h1>
        <p className={styles.subtitle}>欢迎回来，请登录后继续工作</p>

        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              className={styles.loginInput}
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>

          <Form.Item
            className={styles.passwordItem}
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              className={styles.loginInput}
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              登录
            </Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}
