import { NextRequest, NextResponse } from "next/server";

const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8001";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();

    const response = await fetch(
      `${FASTAPI_URL}/api/v1/ppt/regenerate-questions-slide`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: body,
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error("Error in regenerate-questions-slide proxy:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
