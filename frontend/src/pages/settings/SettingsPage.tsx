import { useState, useEffect } from 'react'
import { Table, Card, Space, Button, Tag, Modal, Form, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { useAuthStore } from '../../stores/authStore'
import styles from './SettingsPage.module.css'

interface TagItem {
  id: number
  tag_name: string
  tag_type: string
  created_at: string
}

interface TagListResponse {
  items: TagItem[]
  total: number
}

const tagTypeLabels: Record<string, string> = {
  sales: '销售标签',
  consultant: '咨询标签',
}

const tagTypeColors: Record<string, string> = {
  sales: 'blue',
  consultant: 'green',
}

export default function SettingsPage() {
  const { accessToken } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [tags, setTags] = useState<TagItem[]>([])
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTag, setEditingTag] = useState<TagItem | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchTags()
  }, [])

  const fetchTags = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/v1/tags', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch tags')
      }

      const data: TagListResponse = await response.json()
      setTags(data.items)
    } catch (error) {
      message.error('获取标签列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingTag(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (tag: TagItem) => {
    setEditingTag(tag)
    form.setFieldsValue({
      tag_name: tag.tag_name,
      tag_type: tag.tag_type,
    })
    setModalOpen(true)
  }

  const handleDelete = async (tagId: number) => {
    try {
      const response = await fetch(`/api/v1/tags/${tagId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete tag')
      }

      message.success('删除成功')
      fetchTags()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      if (editingTag) {
        // Update
        const response = await fetch(`/api/v1/tags/${editingTag.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify(values),
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to update tag')
        }

        message.success('更新成功')
      } else {
        // Create
        const response = await fetch('/api/v1/tags', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify(values),
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to create tag')
        }

        message.success('创建成功')
      }

      setModalOpen(false)
      fetchTags()
    } catch (error: any) {
      message.error(error.message || '操作失败')
    }
  }

  const columns: ColumnsType<TagItem> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '标签名称',
      dataIndex: 'tag_name',
      key: 'tag_name',
      render: (name: string, record) => (
        <Tag color={tagTypeColors[record.tag_type] || 'default'}>{name}</Tag>
      ),
    },
    {
      title: '标签类型',
      dataIndex: 'tag_type',
      key: 'tag_type',
      width: 120,
      render: (type: string) => tagTypeLabels[type] || type,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除此标签吗？"
            description="删除后，关联此标签的客户将解除关联"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>系统设置</h2>
      </div>

      <Card title="标签管理" className={styles.card}>
        <div className={styles.toolbar}>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建标签
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={tags}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title={editingTag ? '编辑标签' : '新建标签'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="tag_name"
            label="标签名称"
            rules={[{ required: true, message: '请输入标签名称' }]}
          >
            <Input placeholder="请输入标签名称" maxLength={100} />
          </Form.Item>
          <Form.Item
            name="tag_type"
            label="标签类型"
            rules={[{ required: true, message: '请选择标签类型' }]}
          >
            <Select placeholder="请选择标签类型">
              <Select.Option value="sales">销售标签</Select.Option>
              <Select.Option value="consultant">咨询标签</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
