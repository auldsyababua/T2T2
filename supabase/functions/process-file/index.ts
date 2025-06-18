// Main file processing orchestrator Edge Function
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0"
import { S3Client, GetObjectCommand } from "https://esm.sh/@aws-sdk/client-s3@3.400.0"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ProcessFileRequest {
  fileId: string
  fileType: string
  s3Key: string
  s3Bucket: string
  userId: string
  chatId: string
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    const { fileId, fileType, s3Key, s3Bucket, userId, chatId } = await req.json() as ProcessFileRequest

    console.log(`Processing file: ${fileId} (${fileType}) from ${s3Bucket}/${s3Key}`)

    // Update processing status
    await supabase
      .from('telegram_files')
      .update({
        processing_status: 'processing',
        processing_started_at: new Date().toISOString()
      })
      .eq('id', fileId)

    // Route to appropriate processor based on file type
    let processingResult: any = {}

    switch (fileType) {
      case 'photo':
        processingResult = await processImage(fileId, s3Key, s3Bucket, supabase)
        break
      case 'video':
        processingResult = await processVideo(fileId, s3Key, s3Bucket, supabase)
        break
      case 'audio':
      case 'voice':
        processingResult = await processAudio(fileId, s3Key, s3Bucket, supabase)
        break
      case 'document':
        processingResult = await processDocument(fileId, s3Key, s3Bucket, supabase)
        break
      default:
        processingResult = { skipped: true, reason: 'Unsupported file type' }
    }

    // Generate embedding if we extracted text
    if (processingResult.extractedText) {
      const embedding = await generateEmbedding(processingResult.extractedText)
      
      await supabase
        .from('telegram_files')
        .update({
          extracted_text: processingResult.extractedText,
          content_summary: processingResult.summary,
          content_embedding: embedding,
          metadata: processingResult.metadata || {},
          processing_status: 'completed',
          processing_completed_at: new Date().toISOString()
        })
        .eq('id', fileId)
    } else {
      await supabase
        .from('telegram_files')
        .update({
          processing_status: processingResult.skipped ? 'skipped' : 'completed',
          processing_completed_at: new Date().toISOString(),
          metadata: processingResult.metadata || {}
        })
        .eq('id', fileId)
    }

    // Update cache if frequently accessed
    if (processingResult.extractedText) {
      await updateRedisCache(fileId, {
        extractedText: processingResult.extractedText,
        embedding: embedding,
        fileType: fileType
      })
    }

    return new Response(
      JSON.stringify({ success: true, fileId, processingResult }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Processing error:', error)
    
    // Update status to failed
    if (error.fileId) {
      const supabaseUrl = Deno.env.get('SUPABASE_URL')!
      const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
      const supabase = createClient(supabaseUrl, supabaseServiceKey)
      
      await supabase
        .from('telegram_files')
        .update({
          processing_status: 'failed',
          processing_error: error.message,
          processing_completed_at: new Date().toISOString()
        })
        .eq('id', error.fileId)
    }

    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    )
  }
})

async function processImage(fileId: string, s3Key: string, s3Bucket: string, supabase: any) {
  // Call image processing edge function
  const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/process-image`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fileId, s3Key, s3Bucket })
  })
  
  return await response.json()
}

async function processVideo(fileId: string, s3Key: string, s3Bucket: string, supabase: any) {
  // Call video processing edge function
  const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/process-video`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fileId, s3Key, s3Bucket })
  })
  
  return await response.json()
}

async function processAudio(fileId: string, s3Key: string, s3Bucket: string, supabase: any) {
  // Call audio processing edge function
  const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/process-audio`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fileId, s3Key, s3Bucket })
  })
  
  return await response.json()
}

async function processDocument(fileId: string, s3Key: string, s3Bucket: string, supabase: any) {
  // Call document processing edge function
  const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/process-document`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ fileId, s3Key, s3Bucket })
  })
  
  return await response.json()
}

async function generateEmbedding(text: string): Promise<number[]> {
  const openAIKey = Deno.env.get('OPENAI_API_KEY')!
  
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${openAIKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'text-embedding-ada-002',
      input: text.slice(0, 8000) // Limit text length
    })
  })
  
  const data = await response.json()
  return data.data[0].embedding
}

async function updateRedisCache(fileId: string, data: any) {
  // Update Redis cache via Supabase Redis integration
  // This would connect to your Redis instance
  console.log(`Cache update for ${fileId}:`, data)
  // Implementation depends on your Redis setup
}