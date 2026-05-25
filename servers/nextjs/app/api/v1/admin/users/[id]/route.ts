import { NextRequest, NextResponse } from "next/server";

export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const body = await request.json();

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/admin/users/${params.id}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Cookie: request.headers.get("cookie") || "",
        },
        body: JSON.stringify(body),
      }
    );

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/admin/users/${params.id}`,
      {
        method: "DELETE",
        headers: {
          Cookie: request.headers.get("cookie") || "",
        },
      }
    );

    if (response.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
