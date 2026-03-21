import { useState, useEffect } from 'react'
import { Table, Button, Space, Input, Select, Tag, Modal, Form, message, Drawer } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import styles from './CustomerListPage.module.css'

interface Customer {
  id: number
  name: string
  phone: string | null
  wechat: string | null
  company_name: string | null
  industry: string | null
  source_channel: string | null
  customer_status: string
  owner_user_id: number
  owner_name: string | null
  created_at: string
  updated_at: string
  last_followup_at: string | null
  tags: Array<{ id: number; tag_name: string; tag_type: string }>
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

const statusColors: Record<string, string> = {
  potential: 'default',
  interested: 'blue',
  converted: 'green',
  lost: 'red',
}

const statusLabels: Record<string, string> = {
  potential: '潜在客户',
  interested: '有意向',
  converted: '已转化',
  lost: '已流失',
}

export default function CustomerListPage() {
  const navigate = useNavigate()
  const { user, accessToken } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [tags, setTags] = useState<Array<{ id: number; tag_name: string; tag_type: string }>>([])

  const isAdmin = user?.role_name === 'admin' || user?.role_name === 'super_admin'

  const fetchCustomers = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      })
      if (keyword) params.append('keyword', keyword)
      if (statusFilter) params.append('customer_status', statusFilter)

      const response = await fetch(`/api/v1/customers?${params}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch customers')
      }

      const data: PaginatedResponse<Customer> = await response.json()
      setCustomers(data.items)
      setTotal(data.total)
    } catch (error) {
      message.error('获取客户列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchTags = async () => {
    try {
      const response = await fetch('/api/v1/tags', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })
      if (response.ok) {
        const data = await response.json()
        setTags(data.items)
      }
    } catch (error) {
      console.error('Failed to fetch tags:', error)
    }
  }

  useEffect(() => {
    fetchCustomers()
  }, [page, pageSize, statusFilter])

  useEffect(() => {
    fetchTags()
  }, [])

  const handleSearch = () => {
    setPage(1)
    fetchCustomers()
  }

  const handleCreateCustomer = async (values: any) => {
    try {
      const response = await fetch('/api/v1/customers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(values),
      })

      if (!response.ok) {
        const error = await response.json()
        message.error(error.detail || '创建客户失败')
        return
      }

      message.success('创建客户成功')
      setCreateModalOpen(false)
      form.resetFields()
      fetchCustomers()
    } catch (error) {
      message.error('创建客户失败')
    }
  }

  const columns: ColumnsType<Customer> = [
    {
      title: '客户名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text, record) => (
        <a onClick={() => navigate(`/customers/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      key: 'phone',
      width: 130,
      render: (text) => text || '-',
    },
    {
      title: '公司',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 200,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'customer_status',
      key: 'customer_status',
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status] || 'default'}>
          {statusLabels[status] || status}
        </Tag>
      ),
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags: Customer['tags']) => (
        <Space size={4}>
          {tags?.slice(0, 2).map((tag) => (
            <Tag key={tag.id} color="blue">
              {tag.tag_name}
            </Tag>
          ))}
          {tags?.length > 2 && <span>+{tags.length - 2}</span>}
        </Space>
      ),
    },
    {
      title: '负责人',
      dataIndex: 'owner_name',
      key: 'owner_name',
      width: 100,
      render: (text) => text || '-',
    },
    {
      title: '最后跟进',
      dataIndex: 'last_followup_at',
      key: 'last_followup_at',
      width: 120,
      render: (date: string) => (date ? new Date(date).toLocaleDateString() : '-'),
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" onClick={() => navigate(`/customers/${record.id}`)}>
            详情
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>客户管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)} className={styles.headerButton}>
          新建客户
        </Button>
      </div>

      <div className={styles.filters}>
        <Space>
          <Input
            placeholder="搜索客户名称/手机号/公司"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 250 }}
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="客户状态"
            value={statusFilter}
            onChange={setStatusFilter}
            allowClear
            style={{ width: 120 }}
            options={Object.entries(statusLabels).map(([value, label]) => ({
              value,
              label,
            }))}
          />
          <Button onClick={handleSearch}>搜索</Button>
          <Button onClick={() => { setKeyword(''); setStatusFilter(undefined); setPage(1); fetchCustomers(); }}>
            重置
          </Button>
        </Space>
      </div>

      <div className={styles.tableContainer}>
        <Table
          columns={columns}
          dataSource={customers}
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
        title="新建客户"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateCustomer}
          initialValues={{ customer_status: 'potential' }}
        >
          <Form.Item name="name" label="客户名称" rules={[{ required: true, message: '请输入客户名称' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          <Form.Item name="wechat" label="微信号">
            <Input />
          </Form.Item>
          <Form.Item name="company_name" label="公司名称">
            <Input />
          </Form.Item>
          <Form.Item name="industry" label="行业">
            <Input />
          </Form.Item>
          <Form.Item name="source_channel" label="来源渠道">
            <Input />
          </Form.Item>
          <Form.Item name="customer_status" label="客户状态">
            <Select options={Object.entries(statusLabels).map(([value, label]) => ({ value, label }))} />
          </Form.Item>
          <Form.Item name="tag_ids" label="标签">
            <Select
              mode="multiple"
              options={tags.map(t => ({ value: t.id, label: t.tag_name }))}
              placeholder="选择标签"
            />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">创建</Button>
              <Button onClick={() => setCreateModalOpen(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
