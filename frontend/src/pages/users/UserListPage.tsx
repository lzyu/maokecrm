import { useState, useEffect } from 'react'
import { Table, Button, Space, Input, Select, Tag, Modal, Form, message } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/authStore'
import type { User, PaginatedResponse } from '../../api/generated'
import styles from './UserListPage.module.css'

const roleLabels: Record<string, string> = {
  super_admin: '超级管理员',
  admin: '管理员',
  sales: '销售',
  consultant: '咨询师',
}

export default function UserListPage() {
  const { user: currentUser } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [keyword, setKeyword] = useState('')
  const [roleFilter, setRoleFilter] = useState<number | undefined>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()

  const isSuperAdmin = currentUser?.role_name === 'super_admin'

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (keyword) params.append('keyword', keyword)
      if (roleFilter) params.append('role_id', String(roleFilter))

      const response = await fetch(`/api/v1/users?${params}`, {
        headers: {
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch users')
      }

      const data: PaginatedResponse<User> = await response.json()
      setUsers(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取用户列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [page, pageSize, roleFilter])

  const handleCreateUser = async (values: any) => {
    try {
      const response = await fetch('/api/v1/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
        },
        body: JSON.stringify(values),
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '创建用户失败')
        return
      }

      message.success('创建用户成功')
      setCreateModalOpen(false)
      form.resetFields()
      fetchUsers()
    } catch (error) {
      message.error('创建用户失败')
    }
  }

  const columns: ColumnsType<User> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
      width: 120,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      width: 180,
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
    },
    {
      title: '角色',
      dataIndex: 'role_name',
      key: 'role_name',
      width: 120,
      render: (role: string) => (
        <Tag color={role === 'super_admin' ? 'red' : role === 'admin' ? 'orange' : 'blue'}>
          {roleLabels[role] || role}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>{status === 'active' ? '正常' : '禁用'}</Tag>
      ),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      width: 150,
      render: (date: string) => (date ? new Date(date).toLocaleString() : '-'),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>用户管理</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalOpen(true)}
        >
          新建用户
        </Button>
      </div>

      <div className={styles.filters}>
        <Space>
          <Input
            placeholder="搜索用户名/姓名/邮箱"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={() => fetchUsers()}
            style={{ width: 250 }}
            prefix={<SearchOutlined />}
          />
          <Button onClick={() => fetchUsers()}>搜索</Button>
        </Space>
      </div>

      <div className={styles.tableContainer}>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          scroll={{ x: 'max-content' }}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </div>

      <Modal
        title="新建用户"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateUser}
        >
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Form.Item name="email" label="邮箱">
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input placeholder="请输入手机号" />
          </Form.Item>
          <Form.Item
            name="role_id"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select
              placeholder="请选择角色"
              options={[
                { value: 2, label: '管理员' },
                { value: 3, label: '销售' },
                { value: 4, label: '咨询师' },
              ]}
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                创建
              </Button>
              <Button onClick={() => setCreateModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
