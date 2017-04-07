declare variable $dataset0 external;

<output>
{
    for $in in $dataset0/input/in
    order by string($in) descending
    return <out>{string($in)}</out>
}
</output>
