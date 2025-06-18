// Image processing Edge Function - OCR, object detection, scene analysis
import { serve } from "https://deno.land/std@0.177.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0"
import { S3Client, GetObjectCommand } from "https://esm.sh/@aws-sdk/client-s3@3.400.0"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface ProcessImageRequest {
  fileId: string
  s3Key: string
  s3Bucket: string
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { fileId, s3Key, s3Bucket } = await req.json() as ProcessImageRequest
    
    console.log(`Processing image: ${s3Bucket}/${s3Key}`)

    // Initialize S3 client
    const s3Client = new S3Client({
      region: Deno.env.get('AWS_REGION') || 'us-east-1',
      credentials: {
        accessKeyId: Deno.env.get('AWS_ACCESS_KEY_ID')!,
        secretAccessKey: Deno.env.get('AWS_SECRET_ACCESS_KEY')!,
      },
    })

    // Get image from S3
    const command = new GetObjectCommand({
      Bucket: s3Bucket,
      Key: s3Key,
    })
    
    const s3Response = await s3Client.send(command)
    const imageBuffer = await s3Response.Body?.transformToByteArray()
    
    if (!imageBuffer) {
      throw new Error('Failed to download image from S3')
    }

    // Convert to base64 for API calls
    const base64Image = btoa(String.fromCharCode(...imageBuffer))

    // Parallel processing tasks
    const [ocrResult, visionResult] = await Promise.all([
      performOCR(base64Image),
      analyzeImage(base64Image)
    ])

    // Combine results
    const extractedText = [
      ocrResult.text,
      visionResult.description,
      visionResult.objects?.map(o => o.label).join(', ')
    ].filter(Boolean).join('\n\n')

    const metadata = {
      ocr: {
        text: ocrResult.text,
        confidence: ocrResult.confidence,
        language: ocrResult.language
      },
      vision: {
        objects: visionResult.objects,
        faces: visionResult.faces,
        scene: visionResult.scene,
        colors: visionResult.colors,
        nsfw: visionResult.nsfw
      }
    }

    // Store image metadata
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    )

    await supabase
      .from('image_metadata')
      .upsert({
        file_id: fileId,
        ocr_text: ocrResult.text,
        ocr_confidence: ocrResult.confidence,
        detected_objects: visionResult.objects,
        detected_faces: visionResult.faces?.length || 0,
        scene_description: visionResult.scene,
        dominant_colors: visionResult.colors,
        nsfw_score: visionResult.nsfw?.score || 0,
        is_screenshot: visionResult.isScreenshot || false,
        contains_qr_code: visionResult.hasQRCode || false
      })

    return new Response(
      JSON.stringify({
        extractedText,
        summary: visionResult.description || visionResult.scene,
        metadata
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Image processing error:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 500 }
    )
  }
})

async function performOCR(base64Image: string) {
  // Using OpenAI Vision API for OCR
  const openAIKey = Deno.env.get('OPENAI_API_KEY')!
  
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openAIKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4-vision-preview',
        messages: [{
          role: 'user',
          content: [
            {
              type: 'text',
              text: 'Extract all text from this image. If there is no text, respond with "NO_TEXT_FOUND".'
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:image/jpeg;base64,${base64Image}`
              }
            }
          ]
        }],
        max_tokens: 1000
      })
    })
    
    const data = await response.json()
    const extractedText = data.choices[0].message.content
    
    return {
      text: extractedText === 'NO_TEXT_FOUND' ? '' : extractedText,
      confidence: 0.9, // OpenAI doesn't provide confidence scores
      language: 'en' // Would need separate language detection
    }
  } catch (error) {
    console.error('OCR error:', error)
    return { text: '', confidence: 0, language: null }
  }
}

async function analyzeImage(base64Image: string) {
  // Using OpenAI Vision API for image analysis
  const openAIKey = Deno.env.get('OPENAI_API_KEY')!
  
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${openAIKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4-vision-preview',
        messages: [{
          role: 'user',
          content: [
            {
              type: 'text',
              text: `Analyze this image and provide:
1. A brief description (1-2 sentences)
2. Main objects detected (list)
3. Scene type (indoor/outdoor/screenshot/document/etc)
4. Dominant colors
5. Is it a screenshot? (yes/no)
6. Does it contain a QR code? (yes/no)
7. Number of people/faces visible

Format as JSON.`
            },
            {
              type: 'image_url',
              image_url: {
                url: `data:image/jpeg;base64,${base64Image}`
              }
            }
          ]
        }],
        max_tokens: 500
      })
    })
    
    const data = await response.json()
    const analysisText = data.choices[0].message.content
    
    // Parse the response (assuming GPT-4 returns valid JSON)
    try {
      const analysis = JSON.parse(analysisText)
      return {
        description: analysis.description || '',
        objects: analysis.objects?.map((obj: string) => ({ label: obj, confidence: 0.8 })) || [],
        scene: analysis.scene || 'unknown',
        colors: analysis.colors || [],
        faces: analysis.faces ? Array(analysis.faces).fill({ confidence: 0.8 }) : [],
        isScreenshot: analysis.is_screenshot === 'yes',
        hasQRCode: analysis.has_qr_code === 'yes',
        nsfw: { score: 0 } // Would need separate NSFW detection
      }
    } catch (parseError) {
      // Fallback if JSON parsing fails
      return {
        description: analysisText,
        objects: [],
        scene: 'unknown',
        colors: [],
        faces: [],
        isScreenshot: false,
        hasQRCode: false,
        nsfw: { score: 0 }
      }
    }
  } catch (error) {
    console.error('Image analysis error:', error)
    return {
      description: '',
      objects: [],
      scene: 'unknown',
      colors: [],
      faces: [],
      nsfw: { score: 0 }
    }
  }
}