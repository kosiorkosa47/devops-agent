import { buildConfig } from 'payload/config'
import { postgresAdapter } from '@payloadcms/db-postgres'
import { slateEditor } from '@payloadcms/richtext-slate'
import { s3Adapter } from '@payloadcms/plugin-cloud-storage/s3'
import path from 'path'

export default buildConfig({
  serverURL: process.env.PAYLOAD_PUBLIC_SERVER_URL || 'http://localhost:3001',
  admin: {
    user: 'users',
    meta: {
      titleSuffix: '- DevOps Agent CMS',
      favicon: '/assets/favicon.ico',
      ogImage: '/assets/og-image.jpg',
    },
  },
  collections: [
    {
      slug: 'users',
      auth: true,
      access: {
        read: () => true,
      },
      fields: [
        {
          name: 'role',
          type: 'select',
          required: true,
          defaultValue: 'user',
          options: [
            { label: 'Admin', value: 'admin' },
            { label: 'Editor', value: 'editor' },
            { label: 'User', value: 'user' },
          ],
        },
      ],
    },
    {
      slug: 'pages',
      admin: {
        useAsTitle: 'title',
      },
      access: {
        read: () => true,
      },
      fields: [
        {
          name: 'title',
          type: 'text',
          required: true,
        },
        {
          name: 'slug',
          type: 'text',
          required: true,
          unique: true,
        },
        {
          name: 'content',
          type: 'richText',
        },
        {
          name: 'status',
          type: 'select',
          defaultValue: 'draft',
          options: [
            { label: 'Draft', value: 'draft' },
            { label: 'Published', value: 'published' },
          ],
        },
      ],
    },
    {
      slug: 'media',
      upload: {
        staticURL: '/media',
        staticDir: 'media',
        mimeTypes: ['image/*', 'application/pdf'],
      },
      access: {
        read: () => true,
      },
      fields: [
        {
          name: 'alt',
          type: 'text',
        },
      ],
    },
    {
      slug: 'documentation',
      admin: {
        useAsTitle: 'title',
      },
      fields: [
        {
          name: 'title',
          type: 'text',
          required: true,
        },
        {
          name: 'category',
          type: 'select',
          required: true,
          options: [
            { label: 'Getting Started', value: 'getting-started' },
            { label: 'API Reference', value: 'api-reference' },
            { label: 'Guides', value: 'guides' },
            { label: 'Troubleshooting', value: 'troubleshooting' },
          ],
        },
        {
          name: 'content',
          type: 'richText',
        },
        {
          name: 'order',
          type: 'number',
          defaultValue: 0,
        },
      ],
    },
  ],
  db: postgresAdapter({
    pool: {
      connectionString: process.env.DATABASE_URL || 'postgresql://devops:changeme@localhost:5432/payload_cms',
    },
  }),
  editor: slateEditor({}),
  typescript: {
    outputFile: path.resolve(__dirname, 'payload-types.ts'),
  },
  graphQL: {
    schemaOutputFile: path.resolve(__dirname, 'generated-schema.graphql'),
  },
  plugins: [
    // S3 storage for MinIO
    s3Adapter({
      config: {
        endpoint: process.env.S3_ENDPOINT || 'http://minio.storage.svc.cluster.local:9000',
        region: process.env.S3_REGION || 'us-east-1',
        credentials: {
          accessKeyId: process.env.S3_ACCESS_KEY_ID || 'minioadmin',
          secretAccessKey: process.env.S3_SECRET_ACCESS_KEY || 'changeme',
        },
        forcePathStyle: true,
      },
      bucket: process.env.S3_BUCKET || 'cms-media',
      collections: {
        media: true,
      },
    }),
  ],
})
